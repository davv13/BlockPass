# dapp/tests/test_vault.py
import pytest
from ape import project

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

@pytest.fixture
def owner(accounts):
    # <- note: accept the 'accounts' fixture
    return accounts[0]

@pytest.fixture
def other(accounts):
    return accounts[1]

@pytest.fixture
def vault(owner, project):
    # owner.deploy is shorthand for Vault.deploy(sender=owner)
    return owner.deploy(project.Vault)

def test_create_and_get_items(vault, owner):
    # Initially empty
    assert vault.getMyItems(sender=owner) == []

    # Create two items
    vault.createItem("cid1", "Title One", sender=owner)
    vault.createItem("cid2", "Title Two", sender=owner).wait_for_receipt()

    items = vault.getMyItems(sender=owner)
    assert len(items) == 2
    assert items[0].cid == "cid1" and items[0].title == "Title One"
    assert items[1].cid == "cid2" and items[1].title == "Title Two"

def test_delete_item_only_owner(vault, owner, other):
    vault.createItem("cidX", "Secret X", sender=owner).wait_for_receipt()

    # non-owner must revert
    with pytest.raises(Exception):
        vault.deleteItem(0, sender=other)

    # owner can delete
    vault.deleteItem(0, sender=owner).wait_for_receipt()
    deleted = vault.items(0)
    assert deleted.owner == ZERO_ADDRESS

def test_events_emitted(vault, owner):
    # CreateItem → ItemCreated
    receipt = vault.createItem("cidEvt", "EvTitle", sender=owner).wait_for_receipt()
    ev = receipt.decode_logs(vault.ItemCreated)[-1]
    assert ev.owner == owner.address
    assert ev.cid == "cidEvt" and ev.title == "EvTitle"

    # DeleteItem → ItemDeleted
    receipt2 = vault.deleteItem(0, sender=owner).wait_for_receipt()
    ev2 = receipt2.decode_logs(vault.ItemDeleted)[-1]
    assert ev2.itemId == 0 and ev2.owner == owner.address