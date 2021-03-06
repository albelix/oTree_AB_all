from mock.mock import self
from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
# from tables import group

#import random

from otree.constants import BaseConstants
from otree.models import BaseSubsession, BaseGroup, BasePlayer

from otree.db import models
#from otree import widgets
from otree.common import Currency as c, currency_range, safe_json

author = 'Alexis Belianin'

doc = """
PG game with punishment 
"""


class Constants(BaseConstants):
    name_in_url = 'PG_punishment'
    players_per_group = 5
    num_rounds = 8
    endowment = c(100)
    lumpsum = c(160)
    efficiency_factor = 2
    contribution_limits = currency_range(0, endowment, 1) #define range of contribs


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    total_contribution = models.CurrencyField()
    individual_share = models.CurrencyField()
    round_num=models.IntegerField()
    payoff = models.CurrencyField()
    profit = models.CurrencyField()

    def round_number(self):
        return self.subsession.round_number

# before punishment
    def set_payoffs(self):
        self.total_contribution = sum([p.contribution for p in self.get_players()])
        self.individual_share = self.total_contribution * Constants.efficiency_factor / Constants.players_per_group
#        self.my_contribution = [p.contribution for p in self.get_players()] #sum([p.contribution for p in self.in_all_rounds()])
#        self.my_payoff = ([p.payoff for p in self.get_players()])
#        self.mean_contribution=sum([p.contribution for p in self.get_players()])/5
        for p in self.get_players():
            p.payoff = Constants.endowment - p.contribution + self.individual_share


# after punishment
    def set_punpay(self):
        for p in self.get_players():
            p.profit = self.payoff - p.pun - p.puncost
            print('p.payoff_is', p.profit)

class Player(BasePlayer):
    contribution = models.CurrencyField(doc="""The amount contributed by the player""", min=0,max=100) # choices=Constants.contribution_limits) #add this to see schedule of contribs
    my_contribution = models.CurrencyField(doc="""The amount contributed by the player""", )
    my_payoff = models.CurrencyField()
    mean_contribution = models.CurrencyField()
    pun=models.CurrencyField()
    pun_1 = models.CurrencyField(min=0,max=4,initial=0)
    pun_2 = models.CurrencyField(min=0,max=4,initial=0)
    pun_3 = models.CurrencyField(min=0,max=4,initial=0)
    pun_4 = models.CurrencyField(min=0,max=4,initial=0)
    pun_5 = models.CurrencyField(min=0,max=4,initial=0)
    total_contribution = models.CurrencyField()
    my_profit = models.CurrencyField()
    summy_contribution = models.CurrencyField(doc="""Total amount contributed by the player""")
    puncost = models.CurrencyField()

# before punishment
    def my_method(self):
        for p in self.group.get_players():
            self.my_contribution = p.contribution
        for p in self.group.get_players():
            self.my_payoff = p.payoff
        self.mean_contribution=sum([p.contribution for p in self.group.get_players()])/5

# after punishment
    def my_method_tim(self):
        if self.id_in_group == 1:
            self.pun=sum([p.pun_1 for p in self.group.get_players() if p.id_in_group != 1])
            print('p.payoff_is', self.pun)
        if self.id_in_group == 2:
            self.pun=sum([p.pun_2 for p in self.group.get_players() if p.id_in_group != 2])
            print('p.payoff_is', self.pun)
        if self.id_in_group == 3:
            self.pun=sum([p.pun_3 for p in self.group.get_players() if p.id_in_group != 3])
            print('p.payoff_is', self.pun)
        if self.id_in_group == 4:
            self.pun=sum([p.pun_4 for p in self.group.get_players() if p.id_in_group != 4])
            print('p.payoff_is', self.pun)
        else:
            self.pun=sum([p.pun_5 for p in self.group.get_players() if p.id_in_group != 5])
            print('p.payoff_is', self.pun)
        #self.puncost = sum([p.pun for p in self.subsession.get_players()])*0.2
        self.puncost = (self.pun_1 + self.pun_2 + self.pun_3 + self.pun_4 + self.pun_5)*0.2
        for p in self.group.get_players():
            print('p.payoff_is', p.puncost)

    def my_method_1(self):
        self.summy_contribution = sum([p.contribution for p in self.in_all_rounds()])
        self.my_profit = sum([p.profit for p in self.in_all_rounds()])