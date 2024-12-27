import ape
import pytest, logging

logger = logging.getLogger(__name__)

@pytest.fixture
def owner(accounts):
    return accounts[0]

@pytest.fixture
def mock_price_feed(owner, project):
    # Deploy the mock price feed with an initial price of 20,000 and 8 decimals
    return owner.deploy(project.MockPriceFeed, 20000 * 10**8, 8)

@pytest.fixture
def my_contract(owner, project, mock_price_feed):
    initial_seed = "1 ether"
    return owner.deploy(project.Predictify,
                        mock_price_feed.address,
                        initial_seed,
                        value=initial_seed)

def test_initialization(my_contract, owner):
    # Ensure the contract initializes correctly
    assert my_contract.owner() == owner
    assert my_contract.seedAmount() == 10**18  # 1 ether
    assert my_contract.currentRound() == 1


def test_place_bet(my_contract, accounts):
    # Place a bet from a different account
    bettor = accounts[1]
    bet_price = 20000  # Arbitrary predicted price

    # Bet must be placed with exactly 0.01 ether
    with pytest.raises(Exception):
        my_contract.placeBet(bet_price, value="0.005 ether", sender=bettor)

    # Place a valid bet
    receipt = my_contract.placeBet(bet_price, value="0.01 ether", sender=bettor)
    logger.info(f'Gas used by placeBet: {receipt.gas_used}')
    # Verify the bet was recorded
    bet_count = my_contract.getBetCount()
    assert bet_count == 1

def test_end_round_with_mock_price(my_contract, owner, mock_price_feed, accounts, chain):
    # Place bets
    bettor1 = accounts[1]
    bettor2 = accounts[2]
    initial_balance = bettor1.balance
    my_contract.placeBet(20000 * 10**8, value="0.01 ether", sender=bettor1)
    my_contract.placeBet(21000 * 10**8, value="0.01 ether", sender=bettor2)
    assert my_contract.getBetCount() == 2
    # Advance the chain timestamp by 24 hours
    chain.mine(timestamp=chain.pending_timestamp + 24 * 3600)

    # Update the mock price feed to simulate the actual price
    mock_price_feed.setPrice(20500 * 10**8, sender=bettor1)  # Price is 20,500

    # End the round
    receipt = my_contract.endRound(sender=bettor1)
    logger.info(f'Gas used by endRound: {receipt.gas_used}')
    # Verify that the winner is bettor1 (closest to 20,500 and 1st to bet)
    winner = my_contract.roundWinners(1)
    assert winner == bettor1.address

    # Verify that the winner can withdraw
    winnings = my_contract.pendingWithdrawals(winner)
    receipt = my_contract.withdrawWinnings(sender=bettor1)
    logger.info(f'Gas used by withdrawWinnings: {receipt.gas_used}')
    # Verify the winnings are transferred
    assert bettor1.balance > initial_balance
    assert my_contract.pendingWithdrawals(winner) == 0

    # Verify the owner can withdraw accumulated dev fees
    initial_balance = owner.balance
    dev_fee = my_contract.devFeeBalance()
    assert dev_fee > 0
    receipt = my_contract.withdrawDevFee(sender=owner)
    logger.info(f'Gas used by withdrawDevFee: {receipt.gas_used}')
    # Verify the dev fee is transferred
    assert owner.balance > initial_balance
    assert my_contract.devFeeBalance() == 0