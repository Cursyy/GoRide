from .models import Wallet

def wallet_balance(request):
    if request.user.is_authenticated:
        wallet = Wallet.objects.get(user=request.user)
        return {'wallet_balance': wallet.balance}
    return {'wallet_balance': None}