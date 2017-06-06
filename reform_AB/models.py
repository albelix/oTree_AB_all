# -*- coding: utf-8 -*-
# <standard imports>
from __future__ import division

import random

from otree.constants import BaseConstants
from otree.models import BaseSubsession, BaseGroup, BasePlayer

from otree.db import models
from otree import widgets
from otree.common import Currency as c, currency_range, safe_json

# </standard imports>

author = 'Alex'

doc = """
reforming game
"""

class Constants(BaseConstants):
    name_in_url = 'reform_AB'
    players_per_group = 5
    num_rounds = 5
    base_sales = 10 #16
    base_consumption = 0 # 4
    reform_penalty = 2.5 #4
    reform_benefits = 1 # 0.5
    approval_cost = 0 # 0.3
    solidarity_benefits = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0} # {0: 0.0, 1: 0.2, 2: 0.5, 3: 1, 4: 1.6, 5: 2.3}
    points_to_overthrow = 30 # 6
    max_overthrow_vote_for_player = 5 # 5
    max_reforms = 5
    losses_from_overthrow = 0 # 10
    losses_from_chaos = 0 # 5
    cost_reforms_reversal = 2.5
    payoff_reforms_reversal = base_sales * num_rounds - cost_reforms_reversal


class Subsession(BaseSubsession):
    # need to introduce reforms participant var in order for them to carry over to next rounds. The same thing with overthrow switch.
    # regarding reformed_this_round -- this is ugly, but I couldn't come up with a way to create indicator of whether a player was reformed this round without p.participant.vars
    def before_session_starts(self):
#        random.shuffle()
        if self.round_number == 1:
            for p in self.get_players():
                p.participant.vars['reforms'] = 0
                p.participant.vars['reformed_this_round'] = 0
                p.participant.vars['reformed_previous_round'] = 0
                p.participant.vars['called_to_be_reformed'] = 0
            self.subsession.vars['overthrow'] = 0 # if no reform, 1 if took place, 2 if final reform reversal
            self.subsession.vars['overthrow_round'] = 0
            self.subsession.vars['coordinated_reforms'] = 0
            self.subsession.vars['total_approvals'] = 0
            self.subsession.vars['total_approvals_previous_round'] = 0
            self.subsession.vars['num_approved_reforms'] = 0


class Group(BaseGroup):
    # before the overthrow, number of reforms is equal to round number
    # refapproved=models.IntegerField()
    # refcalled=models.IntegerField()
    # refpastcalled=models.IntegerField()

    def num_reforms(self):
        return self.subsession.round_number

    reformed_id = 0
    # pick one player to be reformed
    def reformed_player(self):
        print("get_player_by_id, before while", self.reformed_id)
        while True:
            self.reformed_id = random.randint(1,Constants.players_per_group)
            print("random id draw", self.reformed_id)
            if self.num_reforms()  \
                    - self.get_player_by_id(self.reformed_id).participant.vars['called_to_be_reformed']*Constants.players_per_group > 0:
                print("check", self.num_reforms() - self.get_player_by_id(self.reformed_id).participant.vars['called_to_be_reformed']*Constants.players_per_group)
                    # - self.get_player_by_id(self.reformed_id).participant.vars['reforms']*Constants.players_per_group > 0:
                # break runs if if is satisfied i.e. we picked the "right" player to reform
                # session.vars['num_approved_reforms'] + 1  - more general. As now, won't work for more than 5 reforms
                print("get_player_by_id, before set", self.reformed_id)
                self.get_player_by_id(self.reformed_id).participant.vars['called_to_be_reformed'] = 1
                print("get_player_by_id, after set", self.reformed_id)
                break

        for p in self.get_players():
            if p.id_in_group == self.reformed_id:
                p.participant.vars['reformed_this_round'] = 1
            # remember that if "if" was satisfied, all next conditions are ignored
            elif p.participant.vars['reformed_this_round'] == 1:
                p.participant.vars['reformed_previous_round'] = 1
                p.participant.vars['reformed_this_round'] = 0
            else:
                p.participant.vars['reformed_this_round'] = 0
                p.participant.vars['reformed_previous_round'] = 0
            print("number", p)
            print("participants' reformed this round", p.participant.vars['reformed_this_round'])
            print("participants' reformed previous round",  p.participant.vars['reformed_previous_round'])
                #    self.refcalled = 0
            #if self.subsession.round_number!=1:
            #   self.refpastcalled = self.group.in_round(self.round_number-1).refcalled

    def adding_reforms(self):
        for p in self.get_players():
            if p.participant.vars['reformed_this_round'] == 1 and self.subsession.vars['total_approvals'] >= 3:
                p.participant.vars['reforms'] += 1
        print("******p.participant.vars['reforms']", p.participant.vars['reforms'])
        if self.subsession.vars['total_approvals'] >= 3:
            self.subsession.vars['num_approved_reforms'] += 1

    # counting approvals for the government to give according solidarity benefits to everybody
    current_round_reform_approved = True
    def approvals(self):
        self.subsession.vars['total_approvals'] = sum(p.approval for p in self.get_players())
        if sum(p.approval for p in self.get_players()) < 3:
            self.current_round_reform_approved = False

    def approvals_previous_round(self):
        return int(sum(p.in_previous_rounds()[-1].approval for p in self.get_players()))

    # sums up players votes for overthrow and switches regime, if necessary
    def total_votes_for_overthrow(self):
        if sum(p.vote_to_overthrow for p in self.get_players()) >= Constants.points_to_overthrow and self.subsession.vars['overthrow'] == 0:
            self.subsession.vars['overthrow'] = 1 #never takes place under current settings
            self.subsession.vars['overthrow_round'] = self.subsession.round_number
            # chaos loses or something
            for p in self.get_players():
                p.payoff -= Constants.losses_from_overthrow

        return sum(p.vote_to_overthrow for p in self.get_players())

    def final_decision(self):
        if sum(p.approval_final for p in self.get_players()) < 3:
            self.subsession.vars['overthrow'] = 2 #meaning reversal of all reform decisions

    reforms_votes_group = []
    # aggregate proposed number of reforms (after overthrow mechanic)
    def reform(self):
        for p in self.get_players():
            self.reforms_votes_group.append(p.reforms_votes)

    def payoffs(self):
        # normal payoff
        # if self.session.vars['total_approvals'] < 3:
        #     for p in self.get_players():
        #         p.payoff = \
        #             Constants.base_sales
        # elif self.session.vars['overthrow'] == 0:
        # else:
        for p in self.get_players():
            p.payoff = \
                Constants.base_sales \
                - ( p.participant.vars['reforms'] * Constants.reform_penalty ) \
                + (( self.subsession.vars['num_approved_reforms'] - p.participant.vars['reforms'] ) * Constants.reform_benefits)
            print("********payoffs********")
            print("- ( p.participant.vars['reforms'] * Constants.reform_penalty )", ( p.participant.vars['reforms'] * Constants.reform_penalty ))
            print("( self.group.vars['num_approved_reforms'] - p.participant.vars['reforms'] )", ( self.subsession.vars['num_approved_reforms'] - p.participant.vars['reforms'] ))
                    #+ Constants.base_consumption \
                    #- ( p.approval * Constants.approval_cost ) \
                    #+ Constants.solidarity_benefits[self.approvals()]
                    #- p.vote_to_overthrow
        #payoff after overthrow if coordination of reforming achieved
        # elif self.reforms_votes_group.count(self.reforms_votes_group[0]) == len(self.reforms_votes_group):
        #     self.session.vars['coordinated_reforms'] = self.reforms_votes_group[0]
        #     for p in self.get_players():
        #         p.payoff = \
        #             Constants.base_sales \
        #             + Constants.base_consumption \
        #             + self.session.vars['coordinated_reforms'] * Constants.reform_benefits
        # payoff after overthrow if no coordination of reforming achieved
        # else:
        #     self.session.vars['coordinated_reforms'] = 0
        #     for p in self.get_players():
        #         p.payoff = \
        #             Constants.base_sales \
        #             + Constants.base_consumption \
        #             - Constants.losses_from_chaos


class Player(BasePlayer):

    # form showing whether a player approves government's reforms
    approval_choices = ((1, "Одобряю"),(0, "Не одобряю"))
    approval = models.FloatField(widget=widgets.RadioSelect, choices=approval_choices)
    approval_final = models.FloatField(widget=widgets.RadioSelect, choices=approval_choices)

    # form showing how much a player is spending on trying to overthrow the system
    vote_to_overthrow = models.FloatField(widget=widgets.SliderInput(attrs={'step': '1'}), min=0, max=Constants.max_overthrow_vote_for_player, default=3)

    # form showing how much reforms a player desires after the overthrow
    reforms_votes = models.FloatField(widget=widgets.SliderInput(attrs={'step': '1'}), min=0, max=Constants.max_reforms, default=3)

    # def approvalFinal(self):
    #     if sum(p.approvalFinal for p in self.get_players()) >= 3:
    #         return 1
    #     else:
    #         return 0
