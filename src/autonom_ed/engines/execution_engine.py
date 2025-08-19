class ExecutionEngine:
    def __init__(self):
        self.last_price = None

    def on_price(self, price: float):
        self.last_price = price

    def execute_immediate(self, target_weight: float):
        # Paper fill at last_price
        if self.last_price is None:
            raise RuntimeError("No price to execute against.")
        return {"price": float(self.last_price), "target_weight": float(target_weight)}
