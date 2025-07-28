import random
import multiprocessing
import math
import time

# Configuration
headless = True
simulations = 10000
num_decks = 8
shuffle_perc = 25.0 + random.random()*25  # Reshuffle when less than this % of cards remain

def simulate(queue, batch_size):
    def new_deck():
        std_deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4 * num_decks
        random.shuffle(std_deck)
        return std_deck[:]

    def draw_card(deck):
        if not deck:
            deck.extend(new_deck())
        return deck.pop(0)

    def hand_value(cards):
        total = sum(cards)
        aces = cards.count(11)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def play_sub_hand(player, dealer, deck):
        bet = 1

        # Double down logic (simple version: always double down on 2 cards)
        if len(player) == 2:
            player.append(draw_card(deck))
            bet *= 2
            return resolve_hand(player, dealer, deck, bet)

        # Hit until 21 or bust
        while hand_value(player) < 21:
            player.append(draw_card(deck))

        return resolve_hand(player, dealer, deck, bet)

    def resolve_hand(player, dealer, deck, bet):
        # Dealer hits on soft 17
        while True:
            d_val = hand_value(dealer)
            if d_val < 17:
                dealer.append(draw_card(deck))
            elif d_val == 17 and 11 in dealer:
                dealer[dealer.index(11)] = 1  # Convert soft 17 to hard 17
            else:
                break

        p_val = hand_value(player)
        d_val = hand_value(dealer)

        if p_val > 21:
            return -1 * bet  # Player busts
        if d_val > 21 or p_val > d_val:
            return 1 * bet   # Player wins
        if p_val == d_val:
            return 0         # Push
        return -1 * bet      # Player loses

    def play_hand(deck):
        dealer = [draw_card(deck), draw_card(deck)]
        player = [draw_card(deck), draw_card(deck)]

        # Check for natural Blackjack
        player_val = hand_value(player)
        dealer_val = hand_value(dealer)

        if player_val == 21 and dealer_val != 21:
            return 1.5  # Blackjack win
        elif player_val == 21 and dealer_val == 21:
            return 0    # Push
        elif dealer_val == 21:
            return -1   # Dealer blackjack

        # Check for possible split
        if player[0] == player[1]:
            split_hand1 = [player[0], draw_card(deck)]
            split_hand2 = [player[1], draw_card(deck)]
            return (
                play_sub_hand(split_hand1, dealer[:], deck)
                + play_sub_hand(split_hand2, dealer[:], deck)
            )
        else:
            return play_sub_hand(player, dealer, deck)

    win = draw = lose = 0
    deck = new_deck()

    for _ in range(batch_size):
        if (float(len(deck)) / (52 * num_decks)) * 100 < shuffle_perc:
            deck = new_deck()

        result = play_hand(deck)

        if result > 1:
            win += 1
        elif result == 1:
            win += 1
        elif result == 0:
            draw += 1
        else:
            lose += 1

    queue.put([win, draw, lose])


if __name__ == '__main__':
    start_time = time.time()
    cpus = multiprocessing.cpu_count()
    batch_size = int(math.ceil(simulations / float(cpus)))

    queue = multiprocessing.Queue()
    processes = []

    for i in range(cpus):
        process = multiprocessing.Process(target=simulate, args=(queue, batch_size))
        processes.append(process)
        process.start()

    for proc in processes:
        proc.join()

    finish_time = time.time() - start_time

    win = draw = lose = 0
    for _ in range(cpus):
        results = queue.get()
        win += results[0]
        draw += results[1]
        lose += results[2]

    print()
    print(f'  cores used: {cpus}')
    print(f'  total simulations: {simulations}')
    print(f'  simulations/s: {int(float(simulations) / finish_time)}')
    print(f'  execution time: {finish_time:.2f}s')
    print(f'  win percentage: {(win / float(simulations)) * 100:.2f}%')
    print(f'  draw percentage: {(draw / float(simulations)) * 100:.2f}%')
    print(f'  lose percentage: {(lose / float(simulations)) * 100:.2f}%')
    print()
