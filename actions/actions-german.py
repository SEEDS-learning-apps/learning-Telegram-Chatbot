import pandas as pd
from typing import Any, Text, Dict, List
import json
from bson import ObjectId

from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.events import SlotSet, EventType, AllSlotsReset, FollowupAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from actions import main
from fuzzywuzzy import process


class ActionUserDataGerman(Action):

    def name(self) -> Text:
        return "action_save_data_german"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # replacing {'key': 'value'} to {"key": "value"} to get valid json
        msg = tracker.latest_message['text'].replace("'", "\"")
        print('msg: ', msg)
        # converting string to json using loads
        try:
            message = json.loads(msg)
            print('message: ', message)
            name: str = message['name']
            id: int = message['id']
            language: str = message['lang']
            print('name: ', name, id, language)
            dispatcher.utter_message(text=f'Hey {name}, how are you doing?')
            return [SlotSet("name", name), SlotSet("id", id), SlotSet("language", language)]
        except:
            print("This is an error!")

        dispatcher.utter_message(text=f"Hey, how are you doing today?")
        return []


global total_subs
global subject_idx
global topic_idx
subject_idx = 0
topic_idx = 0


class ActionTellSubjectsGerman(Action):

    def name(self) -> Text:
        return "action_ask_subj_german"

    @staticmethod
    def user_language():
        pass

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # name = tracker.get_slot('name')
        # print('name: ', name)
        global subject_idx
        global total_subs
        print('subject_idx:', subject_idx)

        if subject_idx == 0:
            total_subs = main.get_subjects(collection_name='subjects')
            subs = [total_subs.pop() for _ in range(5)]
            buttons_subj = [{"title": sub, "payload": '/inform_new{"subj_german":"'+sub+'"}'}
                            for sub in subs]
            buttons_subj.append(
                {"title": 'Next', "payload": '/next_option{"subj_german":"None"}'})

        elif subject_idx != 0:
            if len(total_subs) >= 5:
                subs = [total_subs.pop() for _ in range(5)]
                buttons_subj = [{"title": sub, "payload": '/inform_new{"subj_german":"'+sub+'"}'}
                                for sub in subs]
                buttons_subj.append(
                    {"title": 'Next', "payload": 'next'})

            else:
                subs = [total_subs.pop() for _ in range(len(total_subs))]
                buttons_subj = [{"title": sub, "payload": '/inform_new{"subj_german":"'+sub+'"}'}
                                for sub in subs]

        user_input = tracker.latest_message.get('text')

        fnd, common_value = process.extractOne(user_input, subs)
        print("fnd: ", fnd, 'common value: ', common_value)

        buttons = [{'title': 'Yes', 'payload': '/user_affirm{"subj_german":"'+fnd+'"}'},  # add subject as entity
                   {'title': 'No', 'payload': '/user_deny'}]

        if fnd is not None:

            if common_value >= 70:
                dispatcher.utter_message(
                    text=f"Ich habe in meiner Datenbank {fnd!r} gefunden. Ist es das, was Sie meinen?", buttons=buttons)
                return []

            elif 50 <= common_value < 70:
                dispatcher.utter_message(
                    text=f"Ich glaube, das ist es: {fnd!r}. Ist es das, was Sie meinen?", buttons=buttons)
                return []

        try:
            subject = next(tracker.get_latest_entity_values(
                entity_type="subject"))
        except:
            subject = None

        if subject is not None:
            dispatcher.utter_message(
                text=f"Ich werde meine Datenbank abfragen über {subject}")
            print("Subject: ", subject)
            print(f"Ich werde meine Datenbank abfragen über {subject}")

        else:
            dispatcher.utter_message(
                text=f"Dies sind einige der verfügbaren Themen.", buttons=buttons_subj, button_type="vertical")

        return []


class ActionGiveSuggestionGerman(Action):

    def name(self) -> Text:
        return "action_give_suggestion_german"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        subs = main.get_subjects(collection_name='subjects')

        buttons = [{"title": sub, "payload": '/inform_new{"subj_german":"'+sub+'"}'}
                   for sub in subs]

        dispatcher.utter_message(
            text="Dies sind einige der Themen, die ich vorschlagen würde: ", buttons=buttons)

        return []


class ActionTellTopicsGerman(Action):

    def name(self) -> Text:
        return "action_ask_topic_german"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global topic_idx

        subject = tracker.get_slot('subj_german')
        print('subj -> action_tell_topics: ', subject)

        # if topic_idx == 0:
        topics_available = main.get_topics(subject)
        buttons = [{"title": topic, "payload": '/inform_new{"topic_german":"'+topic_id+'"}'}
                   for topic, topic_id in topics_available.items()]

        dispatcher.utter_message(
            text=f'Bitte wählen Sie ein Thema: ', buttons=buttons, button_type="vertical")

        return []


class ValidateSubmitWithTopicFormGerman(FormValidationAction):

    def name(self) -> Text:
        return "validate_subject_with_topic_form_german"

    def validate_subj_german(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:

        global subject_idx

        intent_value = tracker.get_intent_of_latest_message()

        print('intent_value: ', intent_value)

        print('slot_valuexx->>', slot_value)

        if intent_value == "next_option":
            subject_idx += 1
            return {'subj_german': None}
        print('subject_idx:', subject_idx)
        subject_idx = 0
        return {'subj_german': slot_value}

    def validate_topic_german(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:

        return {'topic_german': slot_value}


class ActionCleanEntity(Action):

    def name(self) -> Text:
        return "action_clean_entity_german"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global i
        i = 0  # reset i before activation of form

        return [SlotSet("subj_german", None), SlotSet("topic_german", None)]


global i
i = 0


class ActionAskQuestionGerman(Action):

    def name(self) -> Text:
        return "action_ask_question_german"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        global i

        topic_id = tracker.get_slot('topic_german')
        print('topic_id: ', topic_id)

        _, questions_available = main.get_questions(topic_id)

        mcq_question = questions_available['mcq_question'][i]
        mcq_choices = questions_available['mcq_choices'][i]
        print('i: ', i, 'mcq_qq: ', mcq_question)
        buttons = [{"title": choice, "payload": f"option{idx+1}"}
                   for idx, choice in enumerate(mcq_choices)]

        dispatcher.utter_message(
            text=mcq_question, buttons=buttons, button_type="vertical")

        return []


class ValidateQuestionsFormGerman(FormValidationAction):

    def name(self) -> Text:
        return "validate_questions_form_german"

    def validate_question_german(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:

        global i
        topic_id = tracker.get_slot('topic_german')
        question_count, questions_available = main.get_questions(topic_id)

        right_answer = questions_available['right_answer'][i]
        pos_feedback = questions_available['feedback']['pos_feedback'][i]
        neg_feedback = questions_available['feedback']['neg_feedback'][i]
        # mcq_choices = questions_available['mcq_choices'][i]

        if slot_value.startswith('/inform_new'):
            return {'question_german': None}
        elif slot_value == right_answer:
            dispatcher.utter_message(text=pos_feedback)
        else:
            dispatcher.utter_message(text=neg_feedback)

        if i < question_count-1:
            i += 1
            print('i ==> ', i, 'question_count ==> ', question_count)
            return {'question_german': None}
        i = 0  # reset value of i to loop again

        return {'question_german': slot_value}

# class ActionTellSubjects(Action):

#     def name(self) -> Text:
#         return "action_ask_subj"

#     @staticmethod
#     def user_language():
#         pass

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         name = tracker.get_slot('name')
#         print('name: ', name)

#         subs = main.get_subjects(collection_name='subjects')

#         user_input = tracker.latest_message.get('text')

#         fnd, common_value = process.extractOne(user_input, subs)
#         print("fnd: ", fnd, 'common value: ', common_value)

#         buttons = [{'title': 'Yes', 'payload': '/user_affirm{"subj":"'+fnd+'"}'},  # add subject as entity
#                    {'title': 'No', 'payload': '/user_deny'}]

#         if fnd is not None:

#             if common_value >= 70:
#                 dispatcher.utter_message(
#                     text=f"I found {fnd!r} in my database. Is that what you mean?", buttons=buttons)
#                 return []

#             elif 50 <= common_value < 70:
#                 dispatcher.utter_message(
#                     text=f"I think this is the one: {fnd}. Is this what you mean?", buttons=buttons)
#                 return []

#         try:
#             subject = next(tracker.get_latest_entity_values(
#                 entity_type="subject"))
#         except:
#             subject = None

#         if subject is not None:
#             dispatcher.utter_message(
#                 text=f"I will query my database about {subject}")
#             print("Subject: ", subject)
#             print(f"I will query my database about {subject}")

#         else:
#             buttons = [{"title": sub, "payload": '/inform_new{"subj":"'+sub+'"}'}
#                        for sub in subs]

#             dispatcher.utter_message(
#                 text=f"I couldn't find anything related to that subject. These are some of the subjects available.", buttons=buttons)

#         return []
