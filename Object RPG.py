# Object RPG
# Guy Turner
# Mar 2 2012 - Mar 14 2012

import random, os.path, cPickle

# -- Begin Global Variables --

combatSpam = True # automatically start game showing fight statistics.

#debug = False # used for debugging of fights

# -- End Global Variables --

#

# -- Begin Class Definitions --

class Chest(object):
    """ A Treasure Chest. """
    def __init__(self, contents = [], lock = True, lockVal = "Med"):
        self.contents = contents
        self.lock = lock
        self.lockVal = lockVal

    def open_chest(self, items, player):
        if self.lock == True:
            print "\tThe chest is locked."
        else:
            print "\tThe chest contains:"
            for item in items:
                print "\t\t" + item.name
            for item in items:
                while True:
                    response = raw_input("\n\tTake " + item.name + "? ")
                    if response.lower() in ("y", "yes"):
                        player.add_item("\t\tYou take ", item)
                        break
                    elif response.lower() in ("n", "no"):
                        print "\t\tYou leave", item.name, "for now."
                        break
                    else:
                        print "\t\tInput not recognized."

class Enemy(object):
    """ An Enemy in the game. """
    def __init__(self, name, kind = "General",
                 basStats = {"Strength": 0, "Wisdom": 0, "Dexterity": 0},
                 advStats = {"Health": 1500, "Max Health": 1500,
                             "Mana": 0, "Max Mana": 0,
                             "Attack Rating": 10, "Mitigation": .10,
                             "Crit Chance": range(6), "Crit Rating": 1.5,
                             "Accuracy": range(76), "Dodge Chance": range(25, 51),
                             "Crit Heal Chance": range(0), "XP": 0},
                 inventory = [], level = 1):
        
        self.hasChest = False # humanoid enemies may be carrying a chest
        self.chests = []
        
        self.invList = {}
        
        self.name = name
        self.kind = kind # Enemy type (General, Animal, Humanoid, etc.)
        self.basStats = basStats
        self.advStats = advStats
        self.inventory = self.populate_inventory()
        self.level = level

        # can the enemy use damage over time abilities
        if self.name.lower() in ("a giant spider"):
            self.hasDOT = True
        else:
            self.hasDOT = False
        self.charges = 0 # for damage over time abilities
        if self.name.lower() in ("a giant spider"):
            self.dmgType = "venom"
        else:
            self.dmgType = "general"
            
        # can the enemy heal
        if self.basStats["Wisdom"] > 0:
            self.healAbility = True
        else:
            self.healAbility = False


    def __str__(self):
        info = self.name + ": Level " + str(self.level) + ", Type: " + self.kind + \
               ". Health = " + str(self.advStats["Health"]) + ", Damage = " + \
               str(self.advStats["Attack Rating"])
        return info

    def attack(self, player, game):
        """ An Enemy attacks the Player. """
        roll = random.randrange(0, 101)
        damage = random.randrange(30, 71)

        #if debug:
        #    print "\tEnemy roll: " + str(roll)
        #    print "\tEnemy damage: " + str(damage)
        #    print "\tEnemy's str: " + str(self.basStats["Strength"])
        #    print "\tEnemy attack mod: " + str(self.advStats["Attack Rating"])

        if self.advStats["Health"] <= (self.advStats["Max Health"] * .30) and \
           self.advStats["Mana"] >= 50 and self.kind == "Humanoid":
            self.heal()
            game.next_turn()

        if (roll in range(50, 76)) and self.hasDOT and player.dotted == False \
           and self.advStats["Mana"] >= 50:
            self.charges = random.randrange(1, 4)
            print "\t" + self.name.capitalize() + " inflicts " + player.name + \
                  " with a " + self.dmgType + "!"
            self.advStats["Mana"] -= 50
            player.dotted = True

        # check for DOTs
        if self.charges > 0:
            self.dot(self.dmgType,
                    ("\t" + self.name.capitalize() + "'s " + self.dmgType + " runs its course."), player)

        if game.turn == 0:
            if roll in player.advStats["Dodge Chance"]:
                print "\t" + player.name + " dodges!"
                game.next_turn()
            elif roll in self.advStats["Accuracy"]:
                if roll in self.advStats["Crit Chance"]:
                    damage = (damage * self.advStats["Crit Rating"]) * self.advStats["Attack Rating"]
                    enemy_mit = damage * player.advStats["Mitigation"]
                    player.advStats["Health"] -= damage - enemy_mit
                else:
                    damage = damage * self.advStats["Attack Rating"]
                    enemy_mit = damage * player.advStats["Mitigation"]
                    player.advStats["Health"] -= damage - enemy_mit
                    
                if combatSpam == True:
                    print "\t" + self.name.capitalize() + " hits " + player.name + " for " + str(damage) + " points!"
                    print "\t" + player.name + " mitigates " + str(enemy_mit) + " points."
                    if player.advStats["Health"] > 0:
                        print "\t" + player.name + "'s health is now " + str(player.advStats["Health"]) + "."
                    else:
                        print "\t" + player.name + "'s health is now 0."
                game.next_turn()
            else:
                if combatSpam == True:
                    print "\t" + self.name.capitalize() + " misses!"
                game.next_turn()

    def dot(self, dmgType, endMessage, player):
        """ Damage Over Time abilities. """
        if self.hasDOT:
            if player.advStats["Health"] > 0:
                damage = random.randrange((10 * self.level), (20 * self.level))
                total = damage * self.level
                player.advStats["Health"] -= total
                if combatSpam == True:
                    print "\t" + self.name.capitalize() + "'s " + dmgType + " hits " + player.name + \
                          " for " + str(total) + " hitpoints!"
                self.charges -= 1
                if self.charges == 0:
                    print endMessage
                    player.dotted = False

    def heal(self):
        """ Uses the Wisdom stat to restore the Player's health. """
        if self.healAbility:
            if self.advStats["Mana"] >= 50:
                roll = random.randrange(0, 101) # crit chance
                amount = random.randrange(50, 350) # heal amount
                if roll in self.advStats["Crit Heal Chance"]:
                    self.restore_health("\t" + self.name.capitalize() + \
                                        " critically heals for ",
                                        (((self.basStats["Wisdom"] * amount) * .75) * 1.5))
                else:
                    self.restore_health("\t" + self.name.capitalize() + \
                                        " heals for ",
                                        ((self.basStats["Wisdom"] * amount) * .75))
                print "\t" + self.name.capitalize() + "'s health is now: " + \
                      str(self.advStats["Health"])
                self.advStats["Mana"] -= 50
            

    def restore_health(self, message, amount):
        """ Generic health restoration. """
        self.advStats["Health"] += amount
        if self.advStats["Health"] > self.advStats["Max Health"]:
            self.advStats["Health"] = self.advStats["Max Health"]
        print message + str(amount) + " hitpoints."

    def populate_inventory(self):
        """ Populate's an Enemy's inventory. """
        self.inventory = []
        if self.name == "a giant bat":
            loot_table = (Item("bat wing", "A fleshy bat wing.",
                               .5, "General"),
                          Item("leather strip", "A strip of animal leather.",
                               .75, "General"),
                          Item("flesh", "This seems edible.",
                               .5, "Food"))
        elif self.name == "a giant spider":
            loot_table = (Item("flesh", "This seems edible.",
                               .5, "Food"),
                          Item("spider carapace", "A scaly spider body.",
                               .75, "General"),
                          Item("giant spider leg", "A spindly spider leg.",
                               .25, "General"))
        elif self.name == "a skeleton":
            loot_table = (Item("bone chip", "Pieces of bone.",
                               .25, "General"),
                          Item("skull", "There are no signs of life.",
                               2, "General"))
            chest_contents = (Item("a key", "This could unlock a door.", .25,
                                  "General"),
                            Armor("a battered breastplate",
                                  "This rusty breastplate is dented, but effective.",
                                  15, "Breastplate", {"Strength": 6, "Dexterity": -3,
                                                      "Mitigation": .18}))
        elif self.name == "a desecrated corpse":
            loot_table = (Item("zombie flesh", "A piece of zombie skin.",
                               .10, "General"),
                          Item("eyeball", "A human eyeball.", .05, "General"),
                          Item("a ration", "A soldier's food ration.", .75,
                               "Food"))
            chest_contents = (Armor("a soldier's frock",
                                    "This coat is lightweight, but durable.",
                                    6, "Breastplate", {"Strength": 5, "Dexterity": 3,
                                                        "Mitigation": .12}),
                              Armor("an iron capeline",
                                    "This helmet is made of polished, black metal.",
                                    3, "Helmet", {"Strength": 3, "Wisdom":4,
                                                  "Mitigation": .10}))
        elif self.name == "a heretic":
            loot_table = [Item("spell book page",
                               "A page from a spell book, in a language you cannot read.",
                               .02, "General")]
            chest_contents = (Armor("a necromancer's robe",
                                    "Magic flows through this robe.",
                                    6, "Breastplate", {"Wisdom": 6, "Dexterity": 4,
                                                        "Mitigation": .06}),
                              Weapon("a ritual dagger",
                                    "A slender dagger decorated with gleaming runes.",
                                    3, "Weapon", {"Strength": 2, "Wisdom": 3}, 25))


        pass_one = random.randrange(0, len(loot_table) * 2)
        if pass_one < len(loot_table):
            self.add_item(loot_table[pass_one])
        pass_two = random.randrange(0, len(loot_table) * 2)
        if pass_two < len(loot_table):
            self.add_item(loot_table[pass_two])
        pass_three = random.randrange(0, len(loot_table) * 2)
        if pass_three < len(loot_table):
            self.add_item(loot_table[pass_three])

        if self.kind == "Humanoid":
            chestChance = random.randrange(0, 51)
            if chestChance in range(0, 6):
                item = chest_contents[random.randrange(0, len(chest_contents))]
                self.chests.append(Chest([item], lock = False))
                self.hasChest = True

        return self.inventory

    def add_item(self, item):
        """ Moves an Item into the Enemy's inventory. """
        if item.name in self.invList:
            self.inventory.append(item)
        else:
            self.inventory.append(item)
            self.invList[item.name] = item
            
class Item(object):
    """ An Item (e.g., a weapon, a piece of armor, etc.). """
    def __init__(self, name, description = "", weight = 0, itemType = "General",
                 effects = {}):
        self.name = name
        self.description = description
        self.weight = weight
        self.itemType = itemType
        self.effects = effects

        if self.effects != {}: # Can the item be used?
            self.effect = True
        else:
            self.effect = False

    def get_name(self):
        return self.name

    def __str__(self):
        info = self.name + ": " + self.description + "\n" + "Weight: " + str(self.weight) \
               + ", Effects: "
        for effect in self.effects:
            info += effect + " : " + self.effects[effect]
        return info

    def use(self):
        """ Uses an effect. """
        used = None
        if len(self.effects) == 1:
            for effect in self.effects:
                print "\tYou use: " + effect + "."
                print "\t\t" + self.effects[effect]
                used = effect
        else:
            effectsList = ()
            for effect in self.effects:
                print "\t" + effect + " : " + self.effects[effect]
                effectsList.append(effect)
            while True:
                response = raw_input("\n\tUse which effect? ")
                if response in effectsList:
                    print "\tYou use: " + response + "."
                    print "\t\t" + self.effects[response]
                    used = response
                    break
                else:
                    print "\tThat effect doesn't exist."

        # LIST OF EFFECTS

class Weapon(Item):
    """ A specific type of Item: a Weapon. """
    def __init__(self, name, description = "", weight = 0, itemType = "Weapon",
                 stats = {}, damage = 0):
        self.name = name
        self.description = description
        self.weight = weight
        self.itemType = itemType
        self.stats = stats
        self.damage = damage

    def __str__(self):
        info = self.name + ": " + self.description + "\n" + "Weight: " + str(self.weight)
        info += ", Damage: " + str(self.damage)
        info += "\nStats:"
        for stat in self.stats:
            info += "\t" + stat + " : " + str(self.stats[stat])
        return info

class Armor(Item):
    """ A specific type of Item: Armor. """
    def __init__(self, name, description = "", weight = 0, itemType = "Armor", stats = {}):
        self.name = name
        self.description = description
        self.weight = weight
        self.itemType = itemType
        self.stats = stats

    def __str__(self):
        info = self.name + ": " + self.description + "\n" + "Weight: " + str(self.weight)
        info += "\nStats:"
        for stat in self.stats:
            info += "\t" + stat + " : " + str(self.stats[stat])
        return info

class Player(object):
    """ The Player of the game. """
    def __init__(self, name, basStats = {"Strength": 0, "Wisdom": 0, "Dexterity": 0},
                 advStats = {"Health": 3000, "Max Health": 3000, "Mana": 0,
                             "Max Mana": 0, "Attack Rating": 10,
                             "Mitigation": .15, "Crit Chance": range(6),
                             "Crit Rating": 1.5, "Accuracy": range(76),
                             "Dodge Chance": range(25, 51), "Crit Heal Chance": range(0),
                             "Morality": 0},
                             armor = {"Breastplate": "", "Helmet": "", "Weapon": ""},
                 inventory = {}, level = [1, 0], companions = {}):
        
        self.dead = False # checks player health
        self.dotted = False # checks if player is inflicted with a DOT
        self.healAbility = False
        self.invList = {} # To keep track of items in the inventory.
        self.armorList = {} # To keep track of currently equipped armor.

        self.companion = False # does the player have a companion?

        # experience point variables
        self.__CONTROL = 100
        self.__MOD = .25
        self.currentMod = self.__MOD
        self.currentLvl = self.__CONTROL * self.currentMod
        
        self.name = name
        self.basStats = basStats
        self.advStats = advStats
        self.armor = armor
        self.inventory = inventory
        self.level = level
        self.companions = companions

    def __str__(self):
        info = name + ": Level " + str(level[0])
        return info

    def attack(self, enemy, game):
        """ A Player attacks an Enemy. """
        roll = random.randrange(0, 101)
        damage = random.randrange(30, 71)

        #if debug:
        #    print "\tPlayer roll: " + str(roll)
        #    print "\tPlayer damage: " + str(damage)

        # check for DOTs
        if enemy.charges > 0:
            enemy.dot(enemy.dmgType,
                     ("\t" + enemy.name.capitalize() + "'s " + enemy.dmgType + " runs its course."), self)

        if roll in enemy.advStats["Dodge Chance"]:
            print "\t" + enemy.name.capitalize() + " dodges!"
            game.next_turn()
        elif roll in self.advStats["Accuracy"]:
            if roll in self.advStats["Crit Chance"]:
                damage = (damage * self.advStats["Crit Rating"]) * self.advStats["Attack Rating"]
                enemy_mit = damage * enemy.advStats["Mitigation"]
                enemy.advStats["Health"] -= damage - enemy_mit
            else:
                damage = damage * self.advStats["Attack Rating"]
                enemy_mit = damage * enemy.advStats["Mitigation"]
                enemy.advStats["Health"] -= damage - enemy_mit
                    
            if combatSpam == True:
                print "\t" + self.name + " hits " + enemy.name + " for " + str(damage) + " points!"
                print "\t" + enemy.name.capitalize() + " mitigates " + str(enemy_mit) + " points."
                if enemy.advStats["Health"] > 0:
                    print "\t" + enemy.name.capitalize() + "'s health is now " + str(enemy.advStats["Health"]) + "."
                else:
                    print "\t" + enemy.name.capitalize() + "'s health is now 0."
            game.next_turn()
        else:
            if combatSpam == True:
                print "\t" + self.name + " misses!"
            game.next_turn()

    def dies(self):
        if self.advStats["Health"] <= 0:
            self.dead = True
            print "\nA light rain begins to fall as " + self.name + " returns to the dead."
        return self.dead

    def heal(self):
        """ Uses the Wisdom stat to restore the Player's health. """
        if self.healAbility:
            if self.advStats["Mana"] >= 50:
                roll = random.randrange(0, 101) # crit chance
                amount = random.randrange(50, 350) # heal amount
                if roll in self.advStats["Crit Heal Chance"]:
                    self.restore_health("\tYou critically heal for ", (amount * 1.5))
                else:
                    self.restore_health("\tYou heal for ", amount)
                print "\tYour health is now: " + str(self.advStats["Health"])
                self.advStats["Mana"] -= 50
            else:
                print "\tYou don't have enough mana!"
        else:
            print "\tYou lack the power necessary to complete this action."
            

    def eat(self):
        """ Consumes a Food item to restore health. """
        ate = False
        for item in self.inventory:
            if item.itemType == "Food":
                self.remove_item("\tYou consume: ", item)
                amount = random.randrange(250, 351)
                self.restore_health("\tYou restore ", amount)
                ate = True
                break
        return ate

    def restore_health(self, message, amount):
        """ Generic health restoration. """
        self.advStats["Health"] += amount
        if self.advStats["Health"] > self.advStats["Max Health"]:
            self.advStats["Health"] = self.advStats["Max Health"]
        print message + str(amount) + " hitpoints."

    def gain_XP(self, amount):
        """ Increases the Player's experience points. """
        print "You gain " + str(amount) + " experience points!"
        self.level[1] += amount
        if (self.currentLvl - self.level[1]) > 0:
            print str(self.currentLvl - self.level[1]) + " points to your next level."

    def level_up(self):
        """ Compares experience gained versus experience needed to level up. """
        if self.level[1] >= self.currentLvl:
            print "\a\a\a\tCongratulations! You are now level " + \
                  str(self.level[0] + 1) + "!"
            self.level[0] += 1
            self.level[1] -= self.currentLvl
            self.currentMod += .25
            self.currentLvl = self.__CONTROL * self.currentMod
            if (self.level[0] % 2) == 0:
                print "\tYou feel your life force bolstered by a dark presence."
                self.advStats["Max Health"] += 500
            print "\tYou feel your strength return!"
            while True:
                response = raw_input("\t\tPick a stat to increase: ")
                if response.lower() in ("str", "strength"):
                    self.add_stat("Strength", 1)
                    print "\tYou have increased your strength by one!"
                    break
                elif response.lower() in ("wis", "wisdom"):
                    self.add_stat("Wisdom", 1)
                    print "\tYou have increased your wisdom by one!"
                    if self.basStats["Wisdom"] > 0 and self.healAbility == False:
                        print "\tYou now have the ability to heal."
                        self.healAbility = True
                    break
                elif response.lower() in ("dex", "dexterity"):
                    self.add_stat("Dexterity", 1)
                    print "\tYou have increased your dexterity by one!"
                    break
                else:
                    print "\t\t\tNot a stat."

            self.update_stats()

    def add_morality(self, amount):
        """ Increases the Player's morality. """
        self.advStats["Morality"] += amount
        print "\tYou feel a warmth surround you."

        if self.advStats["Morality"] >= 300:
            self.advStats["Morality"] = 300

    def remove_morality(self, amount):
        """ Decreases the Player's morality. """
        self.advStats["Morality"] -= amount
        print "\tYou feel a dark presence surround you."

        if self.advStats["Morality"] <= -300:
            self.advStats["Morality"] = -300

    def add_companion(self, companion):
        """ Adds a companion to the group. """
        self.companions[companion.name] = companion
        print "\t" + companion.name + " joins the group!"
        self.companion = True

    def remove_companion(self, companion):
        """ Removes a companion from the group. """
        del self.companions[companion.name]
        print "\t" + companion.name + " leaves the group."
        del companion
        self.companion = True

    def loot(self, enemy):
        if enemy.inventory != []:
            for item in enemy.inventory:
                self.add_item("You loot: ", item)
        if enemy.hasChest == True:
            print enemy.name.capitalize() + " drops a chest!"
            for chest in enemy.chests:
                chest.open_chest(chest.contents, self)

    def use_item(self):
        """ Uses an item. """
        self.print_inventory()
        while True:
            response = raw_input("\n\tUse what? ")
            if response in self.invList:
                if self.invList[response].effect:
                    self.invList[response].use()
                    break
                else:
                    print "\n\tThat item has no effect."
                    break
            elif response.lower() in ("nothing", "none", "exit", "quit"):
                break
            else:
                print "\n\tYou aren't carrying that item."
            
    def add_item(self, message, item):
        """ Moves an Item into the Player's inventory. """
        if item.name in self.invList:
            self.inventory[self.invList[item.name]] += 1
        else:
            self.inventory[item] = 1
            self.invList[item.name] = item
        print message + item.name + "."

    def remove_item(self, message, item):
        """ Removes an Item from the Player's inventory. """
        if self.inventory[item] > 1:
            self.inventory[item] -= 1
        else:
            del self.inventory[item]
            del self.invList[item.name]
        print message + item.name + "."

    def add_armor(self, item):
        """ Adds armor pieces into a dictionary for easy access. """
        for category in self.armor:
            if self.armor[category] != "":
                self.armorList[item.name] = item

    def remove_armor(self, item):
        """ Removes armor pieces from the easy-access dictionary. """
        # modify stats
        for category in self.armor:
            if self.armor[category] == item:
                if category.lower() == "weapon":
                    self.advStats["Attack Rating"] = 10 + (self.basStats["Strength"] * \
                                                     (self.basStats["Strength"] / 4))
                for stat in self.armor[category].stats:
                    if stat in self.basStats:
                        self.basStats[stat] -= self.armor[category].stats[stat]
                    else:
                        self.advStats[stat] -= self.armor[category].stats[stat]

        del self.armorList[item.name]
        self.armor[item.itemType] = ""

        self.update_stats()

    def unequip(self):
        """ Moves an Item from the Player's armor to the inventory. """
        self.print_inventory()
        while True:
            response = raw_input("\n\tUn-Equip what? ")
            if response in self.armorList:
                self.add_item("You un-equip: ", self.armor[self.armorList[response].itemType])
                self.remove_armor(self.armorList[response])
                break
            elif response.lower() in ("nothing", "none", "exit", "quit"):
                break
            else:
                print "\tYou don't have that equipped."

    def equip(self):
        """ Move an Item from the Player's inventory to the Player's armor. """
        self.print_inventory()
        equipped = False
        while True:
            response = raw_input("\n\tEquip what? ")
            done = False
            if response in self.invList:
                if self.invList[response].itemType in ("Breastplate", "Helmet", "Weapon"):
                    item = self.invList[response] # For easy access.
                    if self.armor[item.itemType] != "":
                        while True:
                            choice = raw_input("\t\tUn-Equip " + self.armor[item.itemType].name + "? ")
                            if choice.lower() in ("y", "yes"):
                                self.add_item("You un-equip: ", self.armor[item.itemType]) # Move current armor to Inv.
                                self.remove_armor(self.armor[item.itemType])
                                self.remove_item("You equip: ", item)
                                self.armor[item.itemType] = item
                                self.add_armor(item)
                                equipped = True
                                break
                            elif choice.lower() in ("n", "no"):
                                print "\t\tYou leave your item configuration as it is."
                                equipped = True
                                break
                            else:
                                print "\tInput not recognized."
                    else:
                        self.armor[item.itemType] = item # Replace current armor with item.
                        self.remove_item("You equip: ", item)
                        self.add_armor(item)
                        
                        equipped = True
                    break

            if equipped == True:
                break
                        
            if response.lower() in ("nothing", "none", "exit", "quit"):
                done = True
                break
            elif equipped == False:
                print "\tYou can't equip that item."

        if not done:
            # modify stats
            for category in self.armor:
                if self.armor[category] == item:
                    if category.lower() == "weapon":
                        self.advStats["Attack Rating"] = self.armor[category].damage + \
                                                         (self.basStats["Strength"] * \
                                                         (self.basStats["Strength"] / 4))
                    for stat in self.armor[category].stats:
                        if stat in self.basStats:
                            self.basStats[stat] += self.armor[category].stats[stat]
                        else:
                            self.advStats[stat] += self.armor[category].stats[stat]
                    

        self.update_stats()

    def inspect(self):
        self.print_inventory()
        while True:
            response = raw_input("\n\tInspect what? ")
            if response in self.invList:
                print "\n", self.invList[response]
                break
            elif response in self.armorList:
                print "\n", self.armorList[response]
                break
            elif response.lower() in ("nothing", "none", "exit", "quit"):
                break
            else:
                print "\tYou aren't carrying that item."

    def print_stats(self):
        """ Displays the Player's current stats. """
        print "\tYour current health is:", float(self.advStats["Health"]), "/", float(self.advStats["Max Health"])
        print "\tYour current mana is:", float(self.advStats["Mana"]), "/", float(self.advStats["Max Mana"])
        print "\tYou are level:", self.level[0]
        print "\tYour morality:",
        if self.advStats["Morality"] in range(-100, 101):
            print "Neutral"
        elif self.advStats["Morality"] in range(101, 201):
            print "Good"
        elif self.advStats["Morality"] in range(-200, -100):
            print "Bad"
        elif self.advStats["Morality"] in range(201, 301):
            print "Virtuous"
        elif self.advStats["Morality"] in range(-300, -200):
            print "Evil"
        print "\t\t\t---"
        print "\tYour current stats are:"
        for attribute in self.basStats:
            print "\t\t", attribute + ":", self.basStats[attribute]

    def print_inventory(self):
        """ Displays the Player's current inventory. """
        print "\tYou are currently wearing:"
        for item in self.armor:
            if self.armor[item] != "":
                print "\t\t", item + ":",  self.armor[item].name
        print "\t\t\t---"
        print "\tYou are currently carrying:"
        for item in self.inventory:
            print "\t\t", item.name, "x", self.inventory[item]

    def add_stat(self, stat, amount):
        """ Increments a stat. """
        STATS = ("STRENGTH", "WISDOM", "DEXTERITY")
        if stat.upper() in STATS:
            self.basStats[stat.capitalize()] += amount

    def remove_stat(self, stat, amount):
        """ Decrements a stat. """
        STATS = ("STRENGTH", "WISDOM", "DEXTERITY")
        if stat.upper() in STATS:
            self.basStats[stat.capitalize()] -= amount
            if self.basStats[stat.capitalize()] <= 0:
                self.basStats[stat.capitalize()] = 0

    def update_stats(self):
        """ Modifies advanced stats based on basic stats. """
        self.advStats["Dodge Chance"] = range(25, (51 + self.basStats["Dexterity"]))
        self.advStats["Crit Heal Chance"] = range(0, (self.basStats["Wisdom"] * 2))
        self.advStats["Max Mana"] = 100 * (self.basStats["Wisdom"] * .25)
        self.advStats["Attack Rating"] = 10 + self.basStats["Strength"]
                                               
        if self.armor["Weapon"] != "":
            self.advStats["Attack Rating"] += self.armor["Weapon"].damage - 10

        if self.basStats["Wisdom"] > 0 and self.healAbility == False:
            self.healAbility = True
        elif self.basStats["Wisdom"] == 0 and self.healAbility == True:
            self.healAbility = False

        if self.advStats["Health"] >= self.advStats["Max Health"]:
            self.advStats["Health"] = self.advStats["Max Health"]
        if self.advStats["Mana"] >= self.advStats["Max Mana"]:
            self.advStats["Mana"] = self.advStats["Max Mana"]

    def select_stats(self):
        """ Character Creation: Stat Selection. """
        print "\nA heavy fog rolls in as you are stricken by a feeling of dread!"
        print "A grim voice fills your ears:"
        print "\t'Rise, Shadow Knight " + self.name + ", your destiny awaits!'"
        print "\t'What powers do you possess?'"

        ATTRIBUTES = ("STRENGTH", "STR", "WISDOM", "WIS", "DEXTERITY", "DEX")
        points = 20
        used = 0

        choice = None
        while choice != 0:
            print \
            """
            0 - Done
            1 - Show Current Stats
            2 - Add Stats
            3 - Remove Stats"""
            print
            choice = raw_input("Enter a Main Menu Option: ")
    
            if choice == "0": # Done
                if points != 0:
                    print "\tYou still have points to spend."
                    continue
                else:
                    break
            elif choice == "1": # Show current stats
                print "\nYour current stats are: "
                for stat in self.basStats:
                    print "\t", stat, ":", self.basStats[stat]
            elif choice == "2": # Add Stats
                print
                if points <= 0:
                    print "You are out of points."
                else:
                    print "Number of points remaining:", (points - used)
                    print "Stats: Strength, Wisdom, Dexterity"
                    choice = raw_input("\nWhich stat would you like to increase? ")
        
                    while True:
                        if choice.upper() in ATTRIBUTES:
                            while True:
                                try:
                                    amount = int(raw_input("\tBy how much? "))
                                    break
                                except:
                                    continue
                            if choice.lower() in ("str", "strength"):
                                if points - amount < 0:
                                    print "\n\tSorry, you don't have enough points."
                                else:
                                    self.add_stat("Strength", amount)
                                    points -= amount
                                break
                            elif choice.lower() in ("wis", "wisdom"):
                                if points - amount < 0:
                                    print "\n\tSorry, you don't have enough points."
                                else:
                                    self.add_stat("Wisdom", amount)
                                    points -= amount
                                    if self.basStats["Wisdom"] > 0 and self.healAbility == False:
                                        print "\n\tYou now have the ability to heal."
                                        self.healAbility = True
                                break
                            elif choice.lower() in ("dex", "dexterity"):
                                if points - amount < 0:
                                    print "\n\tSorry, you don't have enough points."
                                else:
                                    self.add_stat("Dexterity", amount)
                                    points -= amount
                                break
                            else:
                                print "Fail"
                                break
                        else:
                            print "Sorry, that isn't a valid stat."
                            break
            elif choice == "3": # Remove Stats
                print
                if points >= 20:
                    print "You have all of your points."
                else:
                    print "Number of points remaining: " + str(points - used)
                    print "Stats: Strength, Wisdom, Dexterity"
                    choice = raw_input("\nWhich stat would you like to decrease? ")
            
                    while True:
                        if choice.upper() in ATTRIBUTES:
                            while True:
                                try:
                                    amount = int(raw_input("\tBy how much? "))
                                    break
                                except:
                                    continue
                            if choice.lower() in ("str", "strength"):
                                if (points + amount > 20) or (amount > self.basStats["Strength"]):
                                    print "\n\tSorry, you can't remove that much."
                                else:
                                    self.remove_stat("Strength", amount)
                                    points += amount
                                break
                            elif choice.lower() in ("wis", "wisdom"):
                                if (points + amount > 20) or (amount > self.basStats["Wisdom"]):
                                    print "\n\tSorry, you can't remove that much."
                                else:
                                    self.remove_stat("Wisdom", amount)
                                    points += amount
                                    if self.basStats["Wisdom"] <= 0:
                                        print "\n\tYou no longer have the ability to heal."
                                        self.healAbility = False   
                                break
                            elif choice.lower() in ("dex", "dexterity"):
                                if (points + amount > 20) or (amount > self.basStats["Dexterity"]):
                                    print "\n\tSorry, you can't remove that much."
                                else:
                                    self.remove_stat("Dexterity", amount)
                                    points += amount
                                break
                            else:
                                print "Fail"
                                break
                        else:
                            print "Sorry, that isn't a valid stat."
                            break
            else:
                print "\tSorry, " + choice + " is not a valid choice."

        # Modifications for stats
    
        self.advStats["Dodge Chance"] = range(25, (51 + self.basStats["Dexterity"]))
        self.advStats["Attack Rating"] += (self.basStats["Strength"] * (self.basStats["Strength"] / 4))
        self.advStats["Crit Heal Chance"] = range(0, (self.basStats["Wisdom"] * 2))
        self.advStats["Max Mana"] = 100 * (self.basStats["Wisdom"] * .25)
        self.advStats["Mana"] = self.advStats["Max Mana"]

    # -- DEBUG Methods --
    
    def print_advStats(self):
        """ THIS IS MEANT FOR DEBUG PURPOSES ONLY! """
        for attribute in self.advStats:
            print attribute + ": " + str(self.advStats[attribute])
        print "Able to heal?", self.healAbility
        print self.invList
        print "Armor: ", self.armor
        print self.armorList
        print "Level Info:"
        print "\tCurrent Mod =", self.currentMod
        print "\tCurrent Level Boundary =", self.currentLvl
        print "Companions: "
        for companion in self.companions:
            print companion

class Companion(Player):
    """ A NPC Companion to help the Player fight. """
    
    def die(self):
        if self.advStats["Health"] <= 0:
            self.dead = True
            print "\t" + self.name + " dies."
        return self.dead

class Game(object):
    """ Handles Game elements such as the story and enemy population. """
    def __init__(self):
        self.__progression = 0
        self.__turn = 0

    def create_character(self):
        """ Creates a Player. """
        print "\nThe pale moonlight creeps over a dilapidated tombstone."
        name = raw_input("A name is etched in the stone, barely recognizable: ")

        return Player(name)

    def get_progression(self):
        return self.__progression

    def set_progression(self, progression):
        self.__progression = progression

    progression = property(get_progression, set_progression)

    def next_turn(self):
        if self.__turn == 0:
            self.__turn += 1
        else:
            self.__turn -= 1

    def get_turn(self):
        return self.__turn

    def set_turn(self, value):
        """ Used mainly for companion fights. """
        self.__turn = value

    turn = property(get_turn, set_turn)

    def print_instructions(self):
        """ Displays the Game's instructions. """
        print "\tFollow the on screen directions."
        print "\tType 'walk' to progress the story."
        print "\tNote that objects in [square brackets] often allow interaction."
        print "\tType 'spam' at any time to turn combat messages during fights on/off."
        print "\tIf your wisdom is above 0, type 'heal' to heal yourself."
        print "\tType 'inventory' at any time to see your items."
        print "\tType 'use' at any time to use an item."
        print "\tType 'inspect' at any time to inspect an item."
        print "\tType 'stats' at any time to see your stats."
        print "\tType 'save' at any time to save your game."
        print "\tType 'load' at any time to load your game."
        print "\tType 'exit' at any time to exit the game."

    def fight(self, player, enemy):
        """ A fight. """
        while player.advStats["Health"] > 0 and enemy.advStats["Health"] > 0:               
            if self.turn == 0: # enemy gets to go
                if player.companion == True:
                    for companion in player.companions:
                        if player.advStats["Health"] <= 0:
                            break
                        if not player.companions[companion].dead:
                            enemy.attack(player.companions[companion], self)
                        self.turn = 0
                if player.advStats["Health"] <= 0:
                            break
                enemy.attack(player, self)
            elif self.turn == 1: # player gets to go
                if player.companion == True:
                    for companion in player.companions:
                        if enemy.advStats["Health"] <= 0:
                            break
                        if not player.companions[companion].dead:
                            player.companions[companion].attack(enemy, self)
                        self.turn = 1
                if enemy.advStats["Health"] <= 0:
                            break
                player.attack(enemy, self)

        # determine death
        if player.companion == True:
            for companion in player.companions:
                if player.companions[companion].advStats["Health"] <= 0:
                    player.companions[companion].dies()
        if enemy.advStats["Health"] <= 0:
            print "\t" + enemy.name.capitalize() + " dies."
            player.gain_XP(enemy.advStats["XP"])
            player.level_up()
            if enemy.inventory != []:
                player.loot(enemy)
        elif player.advStats["Health"] <= 0:
            print "\t" + player.name + " dies."
            player.dies()

        self.turn = 0 # reset the turn for the next fight

    def spawn(self, player):
        """ Checks a die roll to determine whether or not to spawn an Enemy. """
        # Enemies Based on Story Progression
        if self.progression < 26:
            ENEMIES = ("a giant bat", "a skeleton")
            name = ENEMIES[random.randrange(0, len(ENEMIES))]
            if name in ("a skeleton"):
                kind = "Humanoid"
            else:
                kind = "General"
            LEVELS = range(1, 6)
        elif self.progression > 25 and self.progression < 51:
            ENEMIES = ("a skeleton", "a desecrated corpse", "a heretic", "a giant spider")
            name = ENEMIES[random.randrange(0, len(ENEMIES))]
            if name in ("a skeleton", "a desecrated corpse", "a heretic"):
                kind = "Humanoid"
            else:
                kind = "General"
            LEVELS = range(4, 12)
            
        level = random.randrange(1, len(LEVELS))

        # decide experience point values
        if name == "a giant bat":
            xp = 5
        elif name == "a giant spider":
            xp = 8
        elif name == "a skeleton":
            xp = 15
        elif name == "a desecrated corpse":
            xp = 25
        elif name == "a heretic":
            xp = 30
                
                    
        rand = random.randrange(0, 11)
        if rand in range(8):
            # Base Stat generation
            basStats = {"Dexterity":0, "Strength":0, "Wisdom":0}
            
            MODS = (1.5, 2.5, 3.5)
            mod = MODS[random.randrange(0, len(MODS))]
            basStats["Dexterity"] = int(mod * level)
            mod = random.randrange(0, len(MODS))
            basStats["Strength"] = int(mod * level)
            mod = random.randrange(0, len(MODS))
            basStats["Wisdom"] = int(mod * level)

            # Advanced Stat generation
            advStats = {"Health": 0, "Max Health": 0,
                        "Mana": 0, "Max Mana": 0,
                        "Attack Rating": 10, "Mitigation": .10,
                        "Crit Chance": range(6), "Crit Rating": 1.5,
                        "Accuracy": range(76), "Dodge Chance": range(25, 51),
                        "Crit Heal Chance": range(0)}

            advStats["Max Health"] = 1500 * (level * .55)
            advStats["Health"] = advStats["Max Health"]
            advStats["Dodge Chance"] = range(25, (51 + basStats["Dexterity"]))
            advStats["Attack Rating"] += basStats["Strength"]
            advStats["Crit Heal Chance"] = range(0, (basStats["Wisdom"] * 2))
            advStats["Max Mana"] = 100 * (basStats["Wisdom"] * .25)
            advStats["Mana"] = advStats["Max Mana"]

            advStats["XP"] = xp

            inventory = {} # temporary inventory attribute
        
            print "\t" + name.capitalize() + " appears!"
            self.fight(player, Enemy(name, kind, basStats, advStats, inventory, level))
        else:
            print "\tNothing happens."
            return False

    def story(self, player, response):
        """ Handles the Game's plot. """
        # Plot Indicators
        if self.progression == 2:
            print "[Hint: type 'walk' to progress the story.]"
            self.progression += 1
        elif self.progression == 14:
            print "You see a dull [glint] in the distance."
            self.progression += 1
        elif self.progression == 24:
            print "You come across a great, wrought iron [fence]."
            self.progression += 1
        elif self.progression == 30:
            print "You see a field of large, wooden [crosses] in the distance."
            self.progression += 1
        elif self.progression == 37:
            if "Albert" in player.companions:
                print "\nAlbert points off into the distance."
                print "\t'Well, this is it.'"
                print "\t'Thanks again for the help, " + player.name + ", I can't "\
                      "thank you enough.'"
                print "\t'I want you to have this. Don't worry, I've got a spare at the " \
                      "camp!'"
                player.add_item("Albert gives you ", Weapon("a wooden crossbow",
                                                            "A highly effective, long-range weapon.",
                                                            4.5, "Weapon", {"Strength": 5,
                                                                            "Dexterity": 8}, 50))
                print "\t'Good-bye, " + player.name + ".'"
                player.remove_companion(player.companions["Albert"])
            
        # Plot Element
        if self.progression == 0:
            print "\nIt is dark."
            print "You feel an immense weight upon you, but you are compelled to break free!"
            print "You push through the earth above you!"
            print "Suddenly, pale light floods your vision. You emerge in a graveyard."
            player.select_stats()
            self.progression += 1
            return True
        elif self.progression == 1:
            print "\n'Go then, " + player.name + ", and do my bidding!'"
            print "The fog disappears, revealing a [chest].\n"
            self.progression += 1
            save(player, self)
            return True
        elif self.progression > 2 and self.progression < 5:
            if "rusty greatsword" in player.invList:
                progression = 4 # This quest has already been done, move story forward.
                return False
            elif response.lower() in ("chest", "open", "look", "open chest"):
                sword = Weapon("rusty greatsword",
                               "An oddly familiar iron greatsword.",
                               8, "Weapon", {}, 30)
                chest = Chest([sword], False, "None")
                chest.open_chest(chest.contents, player)
                if sword in player.inventory:
                    print "[Hint: type 'equip' to wield your new weapon.]"
                    del chest
                self.progression += 1
                return True
        elif self.progression == 15: # QUEST: The Impaled Head
            if response.lower() in ("glint", "look", "examine"):
                helmet = Armor("a rusty helmet", "This helmet looks rusty, but effective.",
                               2.5, "Helmet", {"Strength": 2, "Wisdom": 3, "Mitigation": .10})
                print "\tThe moon's light reflects off of a battered helmet atop an" \
                      " impaled head."
                print "\tWhat's that?! The head's jaw slowly opens and closes."
                print "\t\t'Ggerrr...'"
                while True:
                    choice = raw_input("\tWhat could it want? ")
                    if choice.lower() in ("feed", "food", "flesh", "eat"): # good morality
                        feed = raw_input("\tFeed the head? ")
                        fed = False
                        if feed.lower() in ("y", "yes"):
                            for item in player.inventory:
                                if item.itemType == "Food":
                                    player.remove_item("\tYou feed the head ", item)
                                    fed = True
                                    print "\tThe head's crooked mouth contorts into a smile."
                                    print "\t\t'Thank...'"
                                    print "\tLife seems to leave the head."
                                    player.add_morality(50)
                                    player.add_item("You claim ", helmet)
                                    self.progression += 1
                                    break
                            if not fed:
                                print "\tYou don't have anything to feed it."
                            break
                        if feed.lower() in ("n", "no"):
                            print "\tYou leave the head for now."
                            break
                        else:
                            print "\tWhat was that?"
                    elif choice.lower() in ("kill", "attack", "destroy"): # bad morality
                        kill = raw_input("\tKill the head? ")
                        if kill.lower() in ("y", "yes"):
                            print "\tThe head's eyes widen in fear as you pick up a nearby rock."
                            while True:
                                confirm = raw_input("\t\tAre you sure you want to do this? ")
                                if confirm.lower() in ("y", "yes"):
                                    print "\tYou beat the life out of the head."
                                    player.remove_morality(75)
                                    player.add_item("You claim ", helmet)
                                    self.progression += 1
                                    break
                                elif confirm.lower() in ("n", "no"):
                                    print "\tYou spare the head for now."
                                    break
                                else:
                                    print "\tWhat was that?"
                            break
                        elif kill.lower() in ("n", "no"):
                            print "\tYou spare the head for now."
                            break
                        else:
                            print "\tWhat was that?"
                    if choice.lower() not in ("feed", "food", "flesh", "eat",
                                              "kill", "attack", "destroy",
                                              "quit", "nothing", "exit"):
                        print "\tThe head doesn't respond."
                    elif choice.lower() in ("quit", "nothing", "exit"):
                        break
        elif self.progression == 25:
            if response.lower() in ("fence", "look", "examine"):
                print "\tThe fence is held shut by heavy, iron chains."
                print "\tYou notice a lock."
                if "a key" in player.invList:
                    while True:
                        choice = raw_input("\tUnlock the fence? ")
                        if choice.lower() in ("y", "yes"):
                            player.remove_item("\tYou open the lock with ",
                                               player.invList["a key"])
                            print "\nYou find yourself atop a large hill looking out upon " \
                                  "an expanse of ruins."
                            print "In the distance, the skeleton of an abandoned monastery " \
                                  "is silhouetted"
                            print "\tagainst the moon."
                            print "\nYou are shrouded in a feeling of dread as a familar " \
                                  "voice fills you head."
                            print "\t'These mortals are defiant.'"
                            print "\t'On the bishop's command, they sent an army to destroy " \
                                  "you...'"
                            print "\t'...drag you into that pit.'"
                            print "\t'Go on, " + player.name + ", but be careful, I have no " \
                                  "power over these undead.'"
                            player.restore_health("An unholy light heals you for ", 10000)
                            self.progression += 1
                            break
                        elif choice.lower() in ("n", "no"):
                            print "\tYou leave the lock for now."
                            break
                        else:
                            print "\tWhat was that?"
                else:
                    print "\tMaybe you can find a way to open the lock."
        elif self.progression == 31: # QUEST: The Crucified Soldier
            if response.lower() in ("crosses", "look", "approach", "examine"):
                print "\tHundreds of ravens fly away as you approach the site."
                print "\tIt appears to be a mass execution, corpses adorn some of the structures."
                while True:
                    action = raw_input("\tYou hear a cry for help! ")
                    if action.lower() in ("y", "yes", "help", "listen", "look", "go"):
                        print "\tA young soldier looks down upon you from a cross."
                        print "\t\t'Jesus! You look worse than me!'"
                        print "\t\t'Listen.. I'm hurt, help me down and I'll repay you.'"
                        while True:
                            choice = raw_input("\t\tWhat will you do? ")
                            if choice.lower() in ("help"): # good morality
                                print "\tYou cut the soldier's bonds."
                                player.add_morality(125)
                                print "\t\t'Thanks, friend.'"
                                print "\t\t'I don't know much about what happened here...'"
                                print "\t\t'I joined the king's army to feed my family, I never " \
                                      "expected to"
                                print "\t\t\tactually have to fight.'"
                                print "\t\t'When word spread that all of this was to kill one man, " \
                                      "some of us"
                                print "\t\t\trefused to go on.'"
                                print "\t\t'The bishop denounced us as heretics and, well.. Here we are.'"
                                print "\t\t'My camp is not far from here, I want to see if anything's left.'"
                                print "\t\t'I'll join you until then and provide some backup.'"
                                print "\tThe soldier pats a heavy crossbow on his back."
                                print "\t\t'By the way, the name's Al.'"
                                player.companion = True
                                soldier = Player("Albert", {"Dexterity": 3, "Strength": 6, "Wisdom": 2},
                                                 {"Health": 3000, "Max Health": 3000, "Mana": 0,
                                                  "Max Mana": 0, "Attack Rating": 10,
                                                  "Mitigation": .15, "Crit Chance": range(6),
                                                  "Crit Rating": 1.5, "Accuracy": range(76),
                                                  "Dodge Chance": range(25, 51), "Crit Heal Chance": range(0),
                                                  "Morality": 0},
                                                 {"Breastplate": Armor("a knight's breastplate",
                                                                       "A pristine breastplate made of polished, black steel.",
                                                                       18, "Breastplate", {"Strength": 9,
                                                                                           "Dexterity": -5,
                                                                                           "Mitigation": .26}),
                                                  "Weapon": Weapon("a wooden crossbow",
                                                                   "A highly effective, long-range weapon.",
                                                                   4.5, "Weapon", {"Strength": 5,
                                                                                   "Dexterity": 8}, 50),
                                                  "Helmet": ""},
                                                 [7, 0], {})
                                soldier.update_stats()
                                player.add_companion(soldier)
                                break
                            elif choice.lower() in ("kill"): # bad morality
                                print "\tYou cut the soldier's bonds."
                                print "\tBefore the soldier can respond, you push your thumbs "\
                                      "into his eye sockets."
                                print "\tA brief cry escapes his lips before he quiets."
                                player.remove_morality(170)
                                print "\tYou dig through his belongings."
                                body = Chest([Item("a ration",
                                                  "A soldier's food ration.", .75,
                                                  "Food"),
                                             Item("a ration",
                                                  "A soldier's food ration.", .75,
                                                  "Food"),
                                             Item("a ration",
                                                  "A soldier's food ration.", .75,
                                                  "Food"),
                                             Armor("a knight's breastplate",
                                                   "A pristine breastplate made of polished, black steel.",
                                                   18, "Breastplate", {"Strength": 9,
                                                                       "Dexterity": -5,
                                                                       "Mitigation": .26}),
                                             Weapon("a wooden crossbow",
                                                    "A highly effective, long-range weapon.",
                                                    4.5, "Weapon", {"Strength": 5,
                                                                    "Dexterity": 8}, 50)],
                                             lock = False)
                                body.open_chest(body.contents, player)
                                break
                            else:
                                print "\t\tWhat was that?"
                        break
                    elif action.lower() in ("n", "no", "ignore", "leave"):
                        break
                    else:
                        print "\tWhat was that?"
                
                

    def walk(self, player):
        """ Progresses the Story. """
        if self.progression != 25: # wait for the Graveyard gate to open
            self.progression += 1
        player.advStats["Health"] += 125 # regenerates health
        if player.advStats["Health"] > player.advStats["Max Health"]:
            player.advStats["Health"] = player.advStats["Max Health"]
        player.advStats["Mana"] += 25 # regenerates mana
        if player.advStats["Mana"] > player.advStats["Max Mana"]:
            player.advStats["Mana"] = player.advStats["Max Mana"]
        self.spawn(player)
            
# -- End Class Definitions --

#

# -- Begin Function Definitions --

def save(player, game):
    """ Saves the player's game. """
    response = raw_input("\tSave your game? ")
    if response.lower() in ("y", "yes"):
        data_file = open(player.name.capitalize() + "_save.dat", "w")
        
        cPickle.dump((player.name, player.level, game.progression, player.invList,
                      player.armorList), data_file)
        cPickle.dump(player.basStats, data_file)
        cPickle.dump(player.advStats, data_file)
        cPickle.dump(player.inventory, data_file)
        cPickle.dump(player.armor, data_file)
        cPickle.dump((player.currentMod, player.currentLvl), data_file)
        cPickle.dump(player.companions, data_file)

        data_file.close()

        print "\tYour game is now saved."

def load(name):
    """ Loads the player's game. """
    data_file = open(name + "_save.dat", "r")

    dat = cPickle.load(data_file)
    basStats = cPickle.load(data_file)
    advStats = cPickle.load(data_file)
    inventory = cPickle.load(data_file)
    armor = cPickle.load(data_file)
    lvlInfo = cPickle.load(data_file)
    companions = cPickle.load(data_file)

    data_file.close()

    info = (Player(dat[0], basStats, advStats, armor, inventory, dat[1]),
            dat[2], dat[3], dat[4])

    game = Game()
    game.progression = dat[2]
    player = Player(dat[0], basStats, advStats, armor, inventory, dat[1], companions)
    player.invList = {}
    for item in player.inventory:
        if item not in player.invList:
            player.invList[item.name] = item
    player.armorList = dat[4]
    player.currentMod = lvlInfo[0]
    player.currentLvl = lvlInfo[1]
    if player.basStats["Wisdom"] > 0:
        player.healAbility = True

    if player.companions != {}:
        player.companion = True

    return (game, player)
    

# -- End Function Definitions --

#

# main

def main():
    global combatSpam
    print "Basic RPG V 1.0"
    print "\tDeveloped by Guy Turner - 2012"
    print "\tLast Updated: Mar 13, 2012"
    print "\tKnown Bugs:"
    print "\t\tSome text wraps awkwardly when using the command prompt."
    print "\t\tCompanions inherit damage over time effects from the player."
    print
    print "Type 'help' at any time for guidance."

    while True:
        response = raw_input("\nWould you like to load? ")
        loaded = False
        if response.lower() in ("y", "yes"):
            while True:
                name = raw_input("What was your character's name? ")
                if os.path.isfile(name.capitalize() + "_save.dat"):
                    info = load(name.capitalize())
                    game = info[0]
                    player = info[1]
                    loaded = True
                    if game.progression > 2:
                        print "[Hint: type 'walk' to progress the story.]"
                    break
                elif name.lower() in ("exit", "quit", "nothing", "no", "n"):
                    break
                else:
                    print "\tThat character has no save.\n"
            if loaded:
                break
        elif response.lower() not in ("y", "yes", "n", "no"):
            print "Invalid response."
        elif response.lower() in ("n", "no"):
            game = Game()
            player = game.create_character()
            break

    response = ""
    while response.lower() != "exit":
        if player.dead:
            break
        if game.story(player, response):
            response = ""
        else:
            response = raw_input(">>> ")
            if response.lower() == "help":
                game.print_instructions()
            elif response.lower() == "inventory":
                player.print_inventory()
            elif response.lower() == "stats":
                player.print_stats()
            elif response.lower() == "inspect":
                player.inspect()
            elif response.lower() == "equip":
                player.equip()
            elif response.lower() == "unequip":
                player.unequip()
            if response.lower() == "use":
                player.use_item()
            elif response.lower() in ("e", "eat"):
                if not player.eat():
                    print "\tYou have nothing to consume."
            elif response.lower() == "heal":
                player.heal()
            elif response.lower() in ("w", "walk"):
                game.walk(player)
            elif response.lower() == "exit":
                save(player, game)
            elif response.lower() == "save":
                save(player, game)
            elif response.lower() == "load":
                info = load(player.name)
                game = info[0]
                player = info[1]
            elif response.lower() == "spam":
                if combatSpam:
                    print "\tCombat Spam is now turned OFF."
                    combatSpam = False
                else:
                    print "\tCombat Spam is now turned ON."
                    combatSpam = True
            elif response == "dBg": # MEANT FOR DEBUGGING
                #if debug:
                #    debug = False
                #    print "Debugging is now off."
                #else:
                #    debug = True
                #    print "Debugging is now on."
                player.print_advStats()

def debug():
    """ MEANT FOR DEBUGGING PURPOSES ONLY! """
    game = Game()
    player = Player("John")

    load("Yulmar")
    player.add_item("", Item("flesh", "This seems edible.",
                               .5, "Food"))
    game.progression = 14
    game.story(player, "look")
    game.walk(player)
    game.story(player, "look")

main()
    
