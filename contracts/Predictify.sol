// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract Predictify {
    struct Bet {
        address bettor;
        int256 predictedPrice; // User's predicted price
    }

    AggregatorV3Interface public priceFeed;
    address public owner;
    uint256 public roundStartTime;
    uint256 public n_bets;
    uint256 immutable betAmount = 0.01 ether; // Fixed bet amount
    uint256 immutable roundDuration = 1 days;
    uint256 immutable betting_duration = 1 hours;
    uint256 public seedAmount; // Current seed for the next round
    uint256 public devFeeBalance; // Accumulated developer fee

    Bet[] public currentRoundBets; // Bets for the current round only
    mapping(uint256 => address) public roundWinners; // Store the winner of each round
    mapping(address => uint256) public pendingWithdrawals; // Winnings available for withdrawal
    // Track if a user has already placed a bet in the current round
    mapping(uint256 => mapping(address => bool)) public hasPlacedBet;
    // Tracks whether a specific price has been bet on in a particular round
    mapping(uint256 => mapping(int256 => bool)) public hasBetOnPrice;

    uint256 public currentRound; // Current round ID

    event RoundStarted(uint256 roundId, uint256 startTime);
    event BetPlaced(
        uint256 roundId,
        address indexed bettor,
        int256 predictedPrice
    );
    event RoundEnded(uint256 roundId, int256 actualPrice, address winner);
    event WinningsWithdrawn(address indexed winner, uint256 amount);
    event DevFeeWithdrawn(address indexed owner, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    constructor(address _priceFeed, uint256 _initialSeed) payable {
        require(msg.value >= _initialSeed, "Insufficient initial seed");
        owner = msg.sender;
        priceFeed = AggregatorV3Interface(_priceFeed);
        seedAmount = _initialSeed;
        currentRound = 1;
        _startNewRound();
    }

    function getPrice() public view returns (int256) {
        (, int256 price, , , ) = priceFeed.latestRoundData();
        return price;
    }

    function getBetCount() public view returns (uint256) {
        return currentRoundBets.length;
    }

    function placeBet(int256 _predictedPrice) external payable {
        require(
            block.timestamp <= roundStartTime + betting_duration,
            "Betting period is over"
        );
        require(msg.value == betAmount, "Bet amount must be 0.01 ETH");
        require(
            !hasPlacedBet[currentRound][msg.sender],
            "You have already placed a prediction in this round"
        );
        require(
            !hasBetOnPrice[currentRound][_predictedPrice],
            "This price has already been bet on"
        );
        currentRoundBets.push(Bet(msg.sender, _predictedPrice));
        hasPlacedBet[currentRound][msg.sender] = true;
        hasBetOnPrice[currentRound][_predictedPrice] = true;
        emit BetPlaced(currentRound, msg.sender, _predictedPrice);
    }

    function endRound() external {
        require(
            block.timestamp >= roundStartTime + roundDuration,
            "Minimum round duration is 24 hours"
        );

        (, int256 _actualPrice, , , ) = priceFeed.latestRoundData();

        // Determine the closest prediction
        address winner;
        int256 closestDifference = type(int256).max;
        Bet[] memory bets = currentRoundBets; // Load into memory
        uint256 length = currentRoundBets.length;
        for (uint256 i = 0; i < length; i++) {
            int256 difference = absoluteDifference(
                bets[i].predictedPrice,
                _actualPrice
            );
            if (difference < closestDifference) {
                closestDifference = difference;
                winner = bets[i].bettor;
            }
        }

        // Distribute prize pool
        if (winner != address(0)) {
            uint256 totalPool = length * betAmount + seedAmount;
            // Calculate fees
            uint256 fee = (totalPool * 10) / 100; // 10% fee
            uint256 devFee = fee / 10; // 1% for dev
            uint256 nextSeed = fee - devFee; // 9% for next round seed
            uint256 prize = totalPool - fee;
            pendingWithdrawals[winner] += prize;
            roundWinners[currentRound] = winner;
            // Update seed and dev fee
            seedAmount = nextSeed;
            devFeeBalance += devFee;
        }

        emit RoundEnded(currentRound, _actualPrice, winner);

        // Automatically start the next round
        delete currentRoundBets; // Clear current round's bets
        currentRound++;
        _startNewRound();
    }

    function withdrawWinnings() external {
        uint256 amount = pendingWithdrawals[msg.sender];
        require(amount > 0, "No winnings to withdraw");

        pendingWithdrawals[msg.sender] = 0;
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");

        emit WinningsWithdrawn(msg.sender, amount);
    }

    function withdrawDevFee() external onlyOwner {
        require(devFeeBalance > 0, "No dev fee to withdraw");

        uint256 amount = devFeeBalance;
        devFeeBalance = 0;
        (bool success, ) = payable(owner).call{value: amount}("");
        require(success, "Transfer failed");
        emit DevFeeWithdrawn(owner, amount);
    }

    function absoluteDifference(
        int256 a,
        int256 b
    ) internal pure returns (int256) {
        unchecked {
            return a > b ? a - b : b - a;
        }
    }

    function _startNewRound() internal {
        roundStartTime = block.timestamp;
        emit RoundStarted(currentRound, roundStartTime);
    }

    receive() external payable {
        revert("Direct ETH transfers not allowed");
    }

    fallback() external payable {
        revert("Direct ETH transfers not allowed");
    }
}
