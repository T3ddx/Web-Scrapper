//SPDX-License-Identifier: MIT

contract Bank {
    mapping(address => uint256) balance;
    mapping(address => bool) disableWithdraw;
    mapping(address => mapping(address => uint256)) allow;

    modifier withdrawAllowed { // reentrancy locking
    require(disableWithdraw[msg.sender] == false); _; }

    function addAllowance(address other, uint256 amnt) public { allow[msg.sender][other] += amnt; }

    function transferFrom(address from,uint256 amnt) withdrawAllowed public {
        require(balance[from] >= amnt);
        require(allow[from][msg.sender] >= amnt);
        balance[from] -= amnt;
        allow[from][msg.sender] -= amnt;
        balance[msg.sender] += amnt; 
    }

    function withdrawBalance() withdrawAllowed public {
        // set lock
        disableWithdraw[msg.sender] = true;
        // reentrant calls possible here
        msg.sender.call{value: balance[msg.sender]}("");
        // release lock
        disableWithdraw[msg.sender] = false;
        balance[msg.sender] = 0; 
    }

    //had to add my own deposit function

    function deposit() public payable{
        balance[msg.sender] += msg.value;
    }
    
    //also added a fallback function
    receive() external payable{
        balance[msg.sender] += msg.value;
    }
}