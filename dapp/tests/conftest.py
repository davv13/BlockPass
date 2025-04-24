# dapp/tests/conftest.py
import ape
import ape.utils.basemodel as _bm

# Grab the original __getattr__ so we can fall back for everything else.
_orig_getattr = _bm.ExtraAttributesMixin.__getattr__

def _patched_getattr(self, name):
    # If someone calls .wait_for_receipt(), just return a function
    # that returns self (the receipt) – no blocking or waiting needed.
    if name == "wait_for_receipt":
        return lambda: self
    # Otherwise defer back to Ape's normal machinery
    return _orig_getattr(self, name)

# Install our patch
_bm.ExtraAttributesMixin.__getattr__ = _patched_getattr
