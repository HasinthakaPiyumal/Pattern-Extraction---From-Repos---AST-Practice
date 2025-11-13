# Cluster 203

def create_dodo_payment(amount: float, plan_name: str, user_email: str):
    """Create payment with Dodo (mock implementation)"""
    payment_id = f'dodo_{secrets.token_hex(8)}'
    dodo_payload = {'amount': amount, 'currency': 'USD', 'description': f'Fincept {plan_name} Plan', 'customer_email': user_email, 'return_url': 'http://localhost:8000/payment/success', 'cancel_url': 'http://localhost:8000/payment/cancel'}
    return {'payment_id': payment_id, 'payment_url': f'https://pay.dodo.com/checkout/{payment_id}', 'status': 'pending'}

