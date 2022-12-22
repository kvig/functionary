from allauth.account.adapter import DefaultAccountAdapter


class FunctionaryAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False

    def add_message(self, *args, **kwargs):
        pass
