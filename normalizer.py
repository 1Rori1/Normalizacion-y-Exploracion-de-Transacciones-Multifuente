import json
import re
from datetime import datetime

class TransactionNormalizer:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def detect_source(self, tx):
        """Detecta la estructura/fuente basándose en las llaves del diccionario."""
        if "id" in tx and "timestamp" in tx:
            return "Fuente_A"
        elif "transaction_id" in tx and "total" in tx:
            return "Fuente_B"
        elif "ref" in tx and "date" in tx:
            return "Fuente_C"
        return "Desconocida"

    def parse_date(self, date_str):
        """Intenta parsear la fecha usando los formatos configurados."""
        if not date_str:
            return None
        date_str = str(date_str).strip()
        for fmt in self.config["date_formats"]:
            try:
                return datetime.strptime(date_str, fmt).isoformat()
            except ValueError:
                continue
        return None

    def clean_amount(self, amount_raw, source, currency):
        """Normaliza el monto según reglas específicas de la fuente."""
        if amount_raw is None:
            return None
        try:
            # Caso Fuente B: Viene en centavos (ej: 10050 -> 100.50)
            if source == "Fuente_B":
                return float(amount_raw) / 100.0
            
            # Caso general: Limpieza de strings (remover €, $, comas por puntos)
            cleaned = re.sub(r'[^\d\.\,]', '', str(amount_raw))
            cleaned = cleaned.replace(',', '.')
            return float(cleaned)
        except ValueError:
            return None

    def normalize_transaction(self, tx):
        """Mapea cualquier estructura al formato unificado requerido."""
        source = self.detect_source(tx)
        if source == "Desconocida":
            return None, "Fuente no identificable"

        # 1. Extraer campos crudos según fuente
        if source == "Fuente_A":
            tx_id = str(tx.get("id"))
            amount_raw = tx.get("amount")
            currency_raw = tx.get("currency")
            date_raw = tx.get("timestamp")
            status_raw = tx.get("status")
        elif source == "Fuente_B":
            tx_id = str(tx.get("transaction_id"))
            amount_raw = tx.get("total")
            currency_raw = tx.get("currency_code")
            date_raw = tx.get("created_at")
            status_raw = tx.get("state")
        elif source == "Fuente_C":
            tx_id = str(tx.get("ref"))
            amount_raw = tx.get("amount")
            # En el ejemplo la moneda puede venir implícita o deducida
            currency_raw = tx.get("currency", "EUR") 
            date_raw = tx.get("date")
            status_raw = tx.get("result")

        # 2. Normalización de Moneda y Estado
        currency = str(currency_raw).upper().strip() if currency_raw else "UNKNOWN"
        status_clean = str(status_raw).lower().strip() if status_raw else ""
        status = self.config["status_mapping"].get(status_clean, "FAILED")

        # 3. Normalización de Monto y Fecha
        amount = self.clean_amount(amount_raw, source, currency)
        timestamp = self.parse_date(date_raw)

        # 4. Validaciones explícitas de consistencia
        errors = []
        if not tx_id: errors.append("ID ausente")
        if amount is None: errors.append("Monto inválido o corrupto")
        if timestamp is None: errors.append("Formato de fecha inválido")
        if currency not in self.config["supported_currencies"]:
            errors.append(f"Moneda '{currency}' no soportada")

        normalized = {
            "id": tx_id,
            "amount": amount,
            "currency": currency,
            "timestamp": timestamp,
            "status": status,
            "source": source
        }

        if errors:
            return {"raw": tx, "errors": errors}, "INVALID"
        return normalized, "VALID"

    def process_file(self, filepath):
        """Procesa un JSON completo devolviendo separados los válidos, inválidos y métricas."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        valid_txs = []
        invalid_txs = []
        
        metrics = {
            "total_processed": 0,
            "total_valid": 0,
            "total_invalid": 0,
            "by_status": {"SUCCESS": 0, "FAILED": 0, "PENDING": 0},
            "by_currency": {}
        }

        for item in data:
            metrics["total_processed"] += 1
            res, classification = self.normalize_transaction(item)
            
            if classification == "VALID":
                valid_txs.append(res)
                metrics["total_valid"] += 1
                # Contador por Estado
                metrics["by_status"][res["status"]] = metrics["by_status"].get(res["status"], 0) + 1
                # Contador por Moneda
                metrics["by_currency"][res["currency"]] = metrics["by_currency"].get(res["currency"], 0) + 1
            else:
                invalid_txs.append(res if res else {"raw": item, "errors": ["Estructura desconocida"]})
                metrics["total_invalid"] += 1

        return valid_txs, invalid_txs, metrics