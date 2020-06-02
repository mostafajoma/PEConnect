pragma solidity ^0.5.0;

import "./FundCCoin.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/release-v2.5.0/contracts/crowdsale/Crowdsale.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/release-v2.5.0/contracts/crowdsale/emission/MintedCrowdsale.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/release-v2.5.0/contracts/crowdsale/validation/CappedCrowdsale.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/release-v2.5.0/contracts/crowdsale/validation/TimedCrowdsale.sol";
import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/release-v2.5.0/contracts/crowdsale/distribution/RefundablePostDeliveryCrowdsale.sol";

// @TODO: Inherit the crowdsale contracts
contract FundCCoinSale is Crowdsale, MintedCrowdsale, CappedCrowdsale, TimedCrowdsale, RefundablePostDeliveryCrowdsale{

    constructor(
        // @TODO: Fill in the constructor parameters!
        uint256 rate,            
        address payable wallet,  
        FundCCoin token,       
        uint256 goal,             
        uint256 open,     
        uint256 close      
        // @TODO: 
    )
        // @TODO: Pass the constructor parameters to the crowdsale contracts.
        Crowdsale(rate, wallet, token)
        MintedCrowdsale()
        CappedCrowdsale(goal)
        TimedCrowdsale(open, close)
        PostDeliveryCrowdsale()
        RefundableCrowdsale(goal)
        // @TODO:
        public
    {
        // constructor can stay empty
    }
}

contract FundCCoinSaleDeployer {

    address public token_sale_address;
    address public token_address;

    constructor(
        // @TODO: Fill in the constructor parameters!
        string memory name,
        string memory symbol,
        address payable wallet, // wallet address will receive all coins raised 
        uint goal
    )
        public
    {
        // @TODO: create the FundCCoin and keep its address handy
        FundCCoin token = new FundCCoin(name, symbol, 0);
        token_address = address(token);

        // @TODO: create the FundCCoinSale and tell it about the token, set the goal, and set the open and close times to now and now + 24 weeks.
        //FundCCoinSale Fund_sale = new FundCCoinSale(1, wallet, token, goal, now, now + 24 weeks);
        FundCCoinSale Fund_sale = new FundCCoinSale(100, wallet, token, goal, now, now + 12 weeks); //to test the time function 
        token_sale_address = address(Fund_sale);
        // make the FundCCoinSale contract a minter, then have the FundCCoinSaleDeployer renounce its minter role
        token.addMinter(token_sale_address);
        token.renounceMinter();
    }
}
