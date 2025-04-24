// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Vault {
    struct Item {
        address owner;
        string cid;
        string title;
        uint256 created;
    }

    Item[] public items;
    mapping(address => uint256[]) public ownerToItems;

    event ItemCreated(
        uint256 indexed itemId,
        address indexed owner,
        string cid,
        string title
    );
    event ItemDeleted(uint256 indexed itemId, address indexed owner);

    function createItem(string calldata cid, string calldata title) external {
        items.push(Item(msg.sender, cid, title, block.timestamp));
        uint256 itemId = items.length - 1;
        ownerToItems[msg.sender].push(itemId);
        emit ItemCreated(itemId, msg.sender, cid, title);
    }

    function getMyItems() external view returns (Item[] memory) {
        uint256[] memory ids = ownerToItems[msg.sender];
        Item[] memory myItems = new Item[](ids.length);
        for (uint256 i = 0; i < ids.length; i++) {
            myItems[i] = items[ids[i]];
        }
        return myItems;
    }

    function deleteItem(uint256 itemId) external {
        require(items[itemId].owner == msg.sender, "Not owner");
        delete items[itemId];
        emit ItemDeleted(itemId, msg.sender);
    }
}
