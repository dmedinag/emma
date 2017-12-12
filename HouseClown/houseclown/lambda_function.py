import logging
import traceback
from .config import fixed_answers

logging.basicConfig(level=logging.DEBUG)


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# --------------- Auxiliary functions for the intent handlers ------------------

def get_slot(intent, key):
    try:
        return intent['slots'][key]['value']
    except KeyError as e:
        logging.error('Missing {} in intent.'.format(e))
        return None



# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Hi, I'm Emma. I'm here for you."
    reprompt_text = "Please tell me what can I help you with."
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you! Have a bright one!"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def entertain(intent, session):

    intent_name = intent['name']
    intent_samples = fixed_answers[intent_name]

    action = get_slot(intent, 'action')
    product = get_slot(intent, 'product')

    logging.info('entertain: action={}, product={}'.format(action, product))

    session_attributes  = {}
    title               = 'Providing some fun'
    speech_output       = 'I need to know what you\'re doing'
    reprompt_text       = 'What is it you\'re going to do?'
    should_end_session  = True

    try:
        valid = None
        for possibility in intent_samples:
            try:
                for k, v in possibility['values'].items():
                    given = get_slot(intent, k)
                    if v is None or given is None:
                        continue
                    if v.lower() != given.lower():
                        raise KeyError
                valid = possibility
            except KeyError:
                continue

        if valid:
            speech_output = valid['expected_response']
        else:
            raise ValueError('Maybe we can rephrase that a bit')

    except ValueError as e:
        logging.error('Failed to handle request: ' + str(e))
        title = 'Error'
        speech_output = str(e)
        reprompt_text = 'Would you please try again?'
    except Exception as e:
        title = 'Error'
        speech_output = 'Sorry, there was an unexpected failure: {}'.format(e)
        logging.critical('entertain: Unexpected error. {}'.format(e))
        traceback.print_exc()
    finally:
        traceback.print_exc()
        return build_response(session_attributes, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """
    logging.info("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """
    logging.info("on_launch requestId=" + launch_request['requestId'] +
                 ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()

def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    logging.info("on_intent requestId=" + intent_request['requestId'] +
                 ", sessionId=" + session['sessionId'] + ", intent=" +
                 intent_request['intent']['name'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name in fixed_answers.keys():
        return entertain(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    logging.info("on_session_ended requestId=" + session_ended_request['requestId'] +
                ", sessionId=" + session['sessionId'])

    # Cleanup:
    session_attributes  = {}
    title               = 'Closing app'
    speech_output       = 'Have a great one!'
    reprompt_text       = None
    should_end_session  = True

    return build_response(session_attributes, build_speechlet_response(
        title, speech_output, reprompt_text, should_end_session))

# --------------- Main handler ------------------

def handler(event, context=None):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    logging.info("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Prevent someone else from configuring a skill that sends requests to this
    function.
    """
    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.fb483e8b-dca3-4258-865c-6e96592a301e"):
        session_attributes  = {}
        title               = 'Error'
        speech_output       = 'Application ID mismatch. Don\'t hack me.'
        reprompt_text       = None
        should_end_session  = True

        return build_response(session_attributes, build_speechlet_response(
            title, speech_output, reprompt_text, should_end_session))

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    try:
        if event['request']['type'] == "LaunchRequest":
            return on_launch(event['request'], event['session'])
        elif event['request']['type'] == "IntentRequest":
            return on_intent(event['request'], event['session'])
        elif event['request']['type'] == "SessionEndedRequest":
            return on_session_ended(event['request'], event['session'])
    except:
        session_attributes  = {}
        title               = 'Error'
        speech_output       = 'Sorry, I can\'t do that'
        reprompt_text       = None
        should_end_session  = True

        return build_response(session_attributes, build_speechlet_response(
            title, speech_output, reprompt_text, should_end_session))
