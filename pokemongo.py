from data import pokemon_dict, moves_dict, types_dict, stats_dict

import random
import copy

### Variables ###############################################
DISPLAY_ALL_MESSAGES = False
# DISPLAY_ALL_MESSAGES = True
RED_COLOR = "#F62222"
BLUE_COLOR = "#0055FF"
STAB_RATIO = 1.25
CRIT_RATIO = 2.0
POKEMON_LIST = stats_dict.keys()
DAMAGE_DAMPEN_MODIFIER = 50.0
DEFAULT_CP = 2000.0
DEFAULT_SIZE = 10
DEFAULT_NUM_BATTLES = 100
BEST_PARTY = ['Vaporeon', 'Vaporeon', 'Vaporeon', 'Vaporeon', 'Vaporeon', 
            'Vaporeon', 'Vaporeon', 'Vaporeon', 'Vaporeon', 'Vaporeon']
BALANCED_PARTY = ['Pidgeot', 'Venusaur', 'Charizard', 'Blastoise', 'Alakazam', 
            'Gengar', 'Magneton', 'Jolteon', 'Nidoking', 'Seel']

### Game Functions ###############################################
def run(mirror=False, size = DEFAULT_SIZE, num = DEFAULT_NUM_BATTLES):
    # simulate_default_single_battle(mirror, size)
    mirror = True
    # num = 10
    simulate_battles(mirror, size, num)

def simulate_default_single_battle(mirror, size):
    # Make Trainer
    red = make_default_trainer("Red", RED_COLOR);
    red.party = make_default_party(cp = DEFAULT_CP, size = size)
    blue = make_default_trainer("Blue", BLUE_COLOR);
    if mirror:
        blue.party = copy.deepcopy(red.party)
    else:
        blue.party = make_default_party(cp = DEFAULT_CP, size = size)
    # Play
    battle(red, blue)

def simulate_battles(mirror, size, num):
    red = make_default_trainer("Red", RED_COLOR);
    blue = make_default_trainer("Blue", BLUE_COLOR);
    red.order_strategy.choose_next_pokemon = active_weakness_order_strat
    red.move_strategy.choose_next_move = highest_dps_choose_next_move
    # blue.order_strategy.choose_next_pokemon = active_weakness_order_strat
    # blue.move_strategy.choose_next_move = highest_dps_choose_next_move
    # Play
    for _ in range(num):
        # red.party = make_default_party(cp = DEFAULT_CP, size = size)
        red.party = make_party_from_list(cp = DEFAULT_CP, party = BALANCED_PARTY)
        if mirror:
            blue.party = copy.deepcopy(red.party)
        else:
            blue.party = make_default_party(cp = DEFAULT_CP, size = size)
        battle(red, blue)

def update_cooldowns(cooldowns):
    if not cooldowns:
        return
    min_cd = min(cooldowns.values())
    to_remove = []
    for k, v in cooldowns.iteritems():
        if v == min_cd:
            to_remove.append(k)
        else:
            cooldowns[k] = round(v-min_cd, 1)
    for k in to_remove:
        cooldowns.pop(k, None)


def battle(red, blue):
    red.reset_before_battle()
    blue.reset_before_battle()
    red.set_opponent(blue)
    blue.set_opponent(red)
    red_first_pokemon = red.choose_next_pokemon(blue)
    blue_first_pokemon = blue.choose_next_pokemon(red)
    red.choose_active_pokemon(red_first_pokemon)
    blue.choose_active_pokemon(blue_first_pokemon)
    
    cooldowns = {}
    # random.shuffle(idle_list)
    # active = idle_list.pop(0)
    while(not game_over(red, blue)):
        update_cooldowns(cooldowns)
        if cooldowns:
            for k, v in cooldowns.iteritems():
                message(k + " is still on cooldown for " + str(v) + " ms before able to attack.")
        draw_state(red, blue)
        active_trainers = get_trainers_off_cooldown([red, blue], cooldowns)
        # random.shuffle(active_trainers)
        for trainer in active_trainers:
            if trainer.active_pokemon and not trainer.active_pokemon.is_fainted():
                next_move = trainer.choose_next_move(trainer.opponent)
                if not next_move:
                    message("* No next move for " + trainer.active_pokemon.name, True)
                    # continue
                damage = trainer.active_pokemon.do_damage(next_move)
                trainer.active_pokemon.change_special_meter(next_move)
                trainer.opponent.active_pokemon.take_damage(damage, get_type_of_attack(next_move))
                cooldowns[trainer.name] = get_duration_of_attack(next_move)
        for trainer in [red, blue]:
            trainer.update()

    finish_game(red, blue)

# Draws the game state. Not implemented
def draw_state(red, blue):
    return

# Checks to see if game is over. Either players have no alive pokes.
def game_over(red, blue):
    return (red.get_alive_count() == 0 or blue.get_alive_count() == 0)

# Handles results, prints stats.
def finish_game(red, blue):
    if (red.get_alive_count() == 0 and blue.get_alive_count() == 0):
        red.tie_game()
        blue.tie_game()
        message("Tie game! Well played by both players.", True)
        message("Stats: \n" + get_battle_stats(red, blue), True)
        return
    elif (red.get_alive_count() > 0):
        winner = red
        loser = blue
    else:
        winner = blue
        loser = red
    winner.win_game()
    loser.lose_game()
    message(winner.name + " has won the battle! \n" + loser.name + " has lost the battle.", True)
    message("Stats: \n" + get_battle_stats(red, blue), True)

# Returns the stats for both players in string format.
def get_battle_stats(red, blue):
    return_string = ""
    for trainer in [red, blue]:
        s = trainer.name + " stats:\n"
        s += "*  Pokemon party: " + trainer.get_party_string() + "\n"
        s += "*  Pokemon alive: " + str(trainer.get_alive_count()) + "\n"
        s += "*  Average health: " + str(trainer.get_average_hp()) + "\n"
        s += "*  Average CP: " + str(trainer.get_average_cp()) + "\n"
        s += "*  Trainer W/L now: " + str(trainer.wlt[0]) + " wins"
        s += " / " + str(trainer.wlt[1]) + " losses"
        s += " / " + str(trainer.wlt[2]) + " ties\n"
        s += "-------------------------------------------\n"
        return_string += s
    return return_string

"""
This is the message function that serves as the print
or print to file function if implemented.
s -- The string to print or print to file.
critical -- If True, will still be printed even if
            DISPLAY_ALL_MESSAGES = False.
"""
def message(s, critical=False):
    if(DISPLAY_ALL_MESSAGES or critical):
        print("-------------------------------------------")
        print(s)

### Utility Functions ###############################################

# Chooses a random pokemon out of all the available PoGo pokemon.
def choose_random_pokemon_all():
    return random.choice(POKEMON_LIST)

# Gets a list of trainers that can attack at this moment.
def get_trainers_off_cooldown(trainers, cooldowns):
    return [t for t in trainers if t.name not in cooldowns]

# Returns type of a move.
def get_type_of_attack(move):
    return moves_dict[move]['Type']

# Returns duration of move in (ms)
def get_duration_of_attack(move):
    return moves_dict[move]['Duration']

# Returns list of types that a type is weak to
def get_weak_to(type):
    info = types_dict[type]
    return [t for t in info.keys() if info[t] > 1.0]

# Returns list of types that a type is strong against
def get_resistant_to(type):
    info = types_dict[type]
    return [t for t in info.keys() if info[t] < 1.0]

# Returns 
def simulate_crit(move):
    prob = moves_dict[move]['Crit']
    return random.random() < prob

def convert_for_crit(n, move):
    prob = moves_dict[move]['Crit']
    if prob >= 1.0:
        return 2.0*n
    return ((1.0-prob)+2.0*(prob)) * n


"""
Takes in two active pokemon (one yours, one opponent's)
and gives back your max dps and the moves that you should use
against your opponent's pokemon.
"""
def get_highest_dps_converted(my_poke, opp_poke):
    best_moves = ['','']
    best_dps = 0.0
    if not my_poke.special:
        # Only mew
        mn_name = my_poke.standard[0]
        mn = moves_dict[mn_name]
        n_dps = my_poke.get_converted_number(mn['DPS'], mn['Type'], opp_poke)
        n_dps = convert_for_crit(n_dps, mn_name)
        return n_dps, [mn_name, '']
    try:
        for mn_name in my_poke.standard:
            for ms_name in my_poke.special:
                mn = moves_dict[mn_name]
                ms = moves_dict[ms_name]
                n_dps = my_poke.get_converted_number(mn['DPS'], mn['Type'], opp_poke)
                n_dps = convert_for_crit(n_dps, mn_name)
                s_dps = my_poke.get_converted_number(ms['DPS'], ms['Type'], opp_poke)
                s_dps = convert_for_crit(s_dps, ms_name)
                recharge_rate = ms['Energy Cost'] / mn['Energy Per Hit']
                s_dps = (recharge_rate * n_dps + s_dps) / (recharge_rate + 1)
                if s_dps > n_dps and s_dps > best_dps:
                    best_dps = s_dps
                    best_moves = [mn_name, ms_name]
                elif n_dps > best_dps:
                    best_dps = n_dps
                    best_moves = [mn_name, '']
        return best_dps, best_moves
    except Exception as e:
        message("** DEBUG: " + str(my_poke.standard))
        message("** DEBUG: " + str(my_poke.special))
        raise e


def default_choose_next_pokemon(me, opp):
    alive = me.get_alive_pokemon()
    if alive:
        return random.choice(alive)
    else:
        return None

def active_weakness_order_strat(me, opp):
    if not opp.active_pokemon:
        return default_choose_next_pokemon(me, opp)
    else:
        my_alive = me.get_alive_pokemon()
        if not my_alive:
            return None
        random.shuffle(my_alive)
        opp_types = opp.active_pokemon.types
        weak_count_dict = {}
        for t in opp_types:
            weaknesses = get_resistant_to(t)
            for t in weaknesses:
                if t in weak_count_dict:
                    weak_count_dict[t] += 1
                else:
                    weak_count_dict[t] = 1
        strong_count_dict = {}
        for t in opp_types:
            strengths = get_weak_to(t)
            for t in strengths:
                if t in strong_count_dict:
                    strong_count_dict[t] += 1
                else:
                    strong_count_dict[t] = 1
        # max_count = max(weak_count_dict.values())
        # keys = weak_count_dict.keys()
        # weakest_types = [t for t in keys if weak_count_dict[t] == max_count]
        best_choice = None
        best_score = None
        for poke in my_alive:
            score = 0.0
            for my_type in poke.types:
                if my_type in weak_count_dict:
                    score += weak_count_dict[my_type]
                if my_type in strong_count_dict:
                    score -= strong_count_dict[my_type]
            if not best_choice or best_score < score:
                best_choice = poke
                best_score = score
        return best_choice


def default_choose_next_move(me, opp):
    active = me.active_pokemon
    if active:
        moves = active.get_available_moves()
        if moves:
            return random.choice(moves)
        else:
            message("***** No moves for " + active.name, True)
    else:
        message("***** Unexpected no active while finding moves!", True)
        return None

def highest_dps_choose_next_move(me, opp):
    if me.active_pokemon and opp.active_pokemon:
        dps, best_moves = get_highest_dps_converted(me.active_pokemon, opp.active_pokemon)
        if not best_moves[1]:
            return best_moves[0]
        else:
            best_special = moves_dict[best_moves[1]]
            if me.active_pokemon.special_meter > best_special['Energy Cost']:
                # Can also use get_available_moves
                return best_moves[1]
            else:
                return best_moves[0]
    else:
        return None

def make_default_trainer(name = "Ash", color=RED_COLOR):
    return Trainer(name=name, color=color)

def make_default_party(cp = DEFAULT_CP, size = DEFAULT_SIZE):
    party = []
    for _ in range(size):
        pkmn = Pokemon(cp=cp)
        party.append(pkmn)
    return party

def make_party_from_list(cp = DEFAULT_CP, party = ["Pidgey"]):
    my_party = []
    for s in party:
        pkmn = Pokemon(name=s, cp=cp)
        my_party.append(pkmn)
    return my_party

"""
Returns a list of the types for the pokemon.
"""
def get_types_for_pokemon(pname):
    if pname in pokemon_dict:
        t = list(pokemon_dict[pname]["Types"])
        return [x for x in t if x]
    else:
        return []

"""
Returns a list of the standard moves for the pokemon.
"""
def get_standard_moves(pname):
    if pname in pokemon_dict:
        t = pokemon_dict[pname]["Standard"]
        return [x for x in t if x]
    else:
        return []

"""
Returns a list of the special moves for the pokemon.
"""
def get_special_moves(pname):
    if pname in pokemon_dict:
        t = pokemon_dict[pname]["Special"]
        return [x for x in t if x]
    else:
        return []

"""
Returns attack, defense, and hp based on CP given.
"""
def get_stats_for_pokemon(name, cp):
    stats = stats_dict[name]
    base = float(stats['Attack'] + stats['Defense'] + stats['Stamina'])
    attack = float(round(cp*stats['Attack']/base, 0))
    defense = float(round(cp*stats['Defense']/base, 0))
    hp = float(round(cp*stats['Stamina']/base, 0))
    return attack, defense, hp

### Clases ###############################################
#
class Pokemon:
    def __init__(self, name=None, cp=1000.0):
        if not name:
            name = choose_random_pokemon_all()
        self.name = name
        self.standard = get_standard_moves(self.name)
        self.special = get_special_moves(self.name)
        self.types = get_types_for_pokemon(self.name)
        self.cp = cp
        hp, attack, defense = get_stats_for_pokemon(self.name, cp)
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.special_meter = 0.0

    """
    Gets converted number (dps or damage) from your poke to their poke.
    n -- dps or damage
    mtype -- move type
    opp_poke -- opponent pokemon
    """
    def get_converted_number(self, n, mtype, opp_poke):
        ratio = 1.0
        for t in opp_poke.types:
            # mtype_converted = mtype.lower()
            # t_converted = t.lower()
            ratio *= types_dict[mtype][t]
        if mtype in self.types:
            ratio *= STAB_RATIO
        return ratio * n

    """
    Subtracts hp off this pokemon.
    Arguments:
    n -- damage given
    type -- string of type that the move trying to damage you does
    damage = ((AttackStat * AttackPower / DefenseStat / 50)+2) * STAB * Effectiveness
    """
    def take_damage(self, n, mtype):
        n = round(n, 1)
        damage = n/float(self.defense) + 2
        ratio = 1.0
        for t in self.types:
            # mtype_converted = mtype.lower()
            # t_converted = t.lower()
            ratio *= types_dict[mtype][t]
        damage = round(damage * ratio, 1)
        output = ""
        output += "*  incoming move has " + str(n) + " power.\n" + "*  Ratio is " + str(ratio)+"\n"
        output += "*  " + self.name + " taking " + str(damage) + " damage after calculations."
        if self.hp > 0.0:
            self.hp = max(0.0, self.hp - damage)
        else:
            output += "*** You are trying to take damage when you're fainted!"
        message(output)

    """
    Calculates damage given.
    damage = ((AttackStat * AttackPower / DefenseStat / 50)+2) * STAB * Effectiveness
    """
    def do_damage(self, move):
        if not move:
            return 0.0
        m = moves_dict[move]
        n = float(m['Power'])
        if m['Type'] in self.types:
            n *= STAB_RATIO
        if simulate_crit(move):
            n *= CRIT_RATIO
        n *= (self.attack / DAMAGE_DAMPEN_MODIFIER)
        return n

    """
    Handles special meter for using a move.
    """
    def change_special_meter(self, move):
        original = self.special_meter
        change_amount = self.calculate_special_meter(move)
        self.add_special_meter(change_amount)
        message("After using " + move + " , special meter went from " + \
                str(original) + " to " + str(self.special_meter) + ".")

    """
    Calculates if you have enough special for a move.
    """
    def calc_enough_special(self, move):
        m = moves_dict[move]
        if m["Energy Cost"]:
            return m["Energy Cost"] <= self.special_meter
        return True

    """
    Calculates special meter increase or not.
    """
    def calculate_special_meter(self, move):
        n = 0.0
        if move in moves_dict:
            m = moves_dict[move]
            if m["Energy Cost"]:
                n -= m["Energy Cost"]
            if m["Energy Per Hit"]:
                n += m["Energy Per Hit"]
        return n

    """
    Adds to special meter.
    """
    def add_special_meter(self, n):
        self.special_meter += n
        self.special_meter = min(100.0, round(self.special_meter, 1))

    """
    Subtracts from special meter.
    """
    def subtract_special_meter(self, n):
        self.special_meter -= n
        self.special_meter = max(0.0, round(self.special_meter, 1))

    """
    Gets list of useable moves.
    """
    def get_available_moves(self):
        available = [move for move in self.special if self.calc_enough_special(move)]
        available += self.standard
        message("*****" + str(available))
        return available

    """
    Returns if pokemon is fainted or not.
    """
    def is_fainted(self):
        return self.hp <= 0.0

class OrderStrategy:
    def __init__(self):
        self.choose_next_pokemon = default_choose_next_pokemon

class MoveStrategy:
    def __init__(self):
        self.choose_next_move = default_choose_next_move

class Trainer:
    # def __init__(self, name = "Ash", color = RED_COLOR):
    #     self.order_strategy = OrderStrategy();
    #     self.move_strategy = MoveStrategy();
    #     self.party = make_default_party();
    #     self.active_pokemon = None
    #     self.wlt = [0, 0, 0]
    #     self.name = name
    #     self.color = color
    #     self.opponent = None

    def __init__(self, order_strategy = None, move_strategy = None, \
                party = make_default_party(), name = "Ash", color = RED_COLOR):
        if not order_strategy:
            strat = OrderStrategy()
            self.order_strategy = strat
        else:
            self.order_strategy = order_strategy
        if not move_strategy:
            strat = MoveStrategy()
            self.move_strategy = strat
        else:
            self.move_strategy = move_strategy
        self.party = party
        self.active_pokemon = None
        self.wlt = [0, 0, 0]
        self.name = name
        self.color = color
        self.opponent = None

    def set_opponent(self, opp):
        self.opponent = opp

    def reset_before_battle(self):
        self.active_pokemon = None

    def get_alive_pokemon(self):
        return [poke for poke in self.party if not poke.is_fainted()]

    def choose_active_pokemon(self, pokemon):
        if pokemon:
            if pokemon.is_fainted():
                self.active_pokemon = None
            else:
                self.active_pokemon = pokemon

    def choose_next_pokemon(self, opp):
        poke = self.order_strategy.choose_next_pokemon(self, opp)
        message(self.name + " sends out " + poke.name + ".")
        return poke

    def choose_next_move(self, opp):
        move = self.move_strategy.choose_next_move(self, opp)
        message(self.name + " chooses " + move + " as the next attack.")
        return move

    def get_alive_count(self):
        count = 0
        for poke in self.party:
            if not poke.is_fainted():
                count += 1
        return count

    def get_average_hp(self):
        return sum([poke.hp for poke in self.party]) / float(len(self.party))

    def get_average_cp(self):
        return sum([poke.cp for poke in self.party]) / float(len(self.party))

    def win_game(self):
        self.wlt[0] += 1

    def lose_game(self):
        self.wlt[1] += 1

    def tie_game(self):
        self.wlt[2] += 1

    def update(self):
        if not self.active_pokemon or self.active_pokemon.is_fainted():
            message(self.name + " does not have an active pokemon. Choosing new pokemon.")
            next_pokemon = self.order_strategy.choose_next_pokemon(self, self.opponent)
            if next_pokemon:
                message(self.name + " chose to send out " + next_pokemon.name)
                self.choose_active_pokemon(next_pokemon)
            else:
                message(self.name + " could not send out a pokemon!")
            message(self.name + " has " + str(self.get_alive_count()) + " pokemon left.")

    """
    Gets string output of trainer's party, with names and CP
    """
    def get_party_string(self):
        output = "["
        for poke in self.party:
            output += '(' + poke.name + ' , ' + str(poke.cp) + ')'
        output += ']'
        return output

if __name__ == '__main__':
    run()