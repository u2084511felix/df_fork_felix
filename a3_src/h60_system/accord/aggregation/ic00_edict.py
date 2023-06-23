# -*- coding: utf-8 -*-
"""
---

title:
    "Discord message aggregation component."

description:
    "Aggregates messages."

id:
    "04fff1bb-ea23-4dc7-a49e-ee3d49415eac"

type:
    dt004_python_stableflow_edict_component

validation_level:
    v00_minimum

protection:
    k00_general

copyright:
    "Copyright 2023 William Payne"

license:
    "Licensed under the Apache License, Version
    2.0 (the License); you may not use this file
    except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed
    to in writing, software distributed under
    the License is distributed on an AS IS BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
    either express or implied. See the License
    for the specific language governing
    permissions and limitations under the
    License."

...
"""


import collections

import fl.util
import key

import fl.net.openai.client


# -----------------------------------------------------------------------------
def coro(runtime, cfg, inputs, state, outputs):  # pylint: disable=W0613
    """
    Transcript aggregation coroutine.

    """

    transcript = collections.defaultdict(list)

    signal = None
    fl.util.edict.init(outputs)
    while True:
        inputs = yield (outputs, signal)
        fl.util.edict.reset(outputs)

        # Keep transcript of messages posted
        # in each channel.
        #
        if inputs['msg']['ena']:
            timestamp = inputs['msg']['ts']
            for msg in inputs['msg']['list']:
                print('MESSAGE: ' + msg['content'])
                transcript[msg['name_channel']].append((timestamp, msg))

        list_request = list()
        if inputs['cmd']['ena']:
            timestamp = inputs['cmd']['ts']
            for cmd in inputs['cmd']['list']:
                id_cmd = cmd['name_command']
                if id_cmd == 'summarize':

                    str_transcript = ''

                    for (name_channel, list_tup_msg) in transcript.items():

                        str_transcript += '\n Channel {name}:\n'.format(
                                                        name = name_channel)

                        for (timestamp, msg) in list_tup_msg:
                            str_transcript += '\n {name}: "{txt}"'.format(
                                                    name = msg['name_author'],
                                                    txt  = msg['content'])

                        str_transcript += '\n'

                    str_transcript += '\n'

                    str_prompt = """Provide a summary for the given transcript from a deliberation session. 
                    Start the summary with the topic of the deliberation session. 
                    Then provide a list of the key arguments and points that have been raised. 
                    Next to each point rasied name the person who raised it, and those who support it.
                    """

                    usr_prompt = f"""
                    {str_transcript}
                    """.format(str_transcript = str_transcript)

                    list_request.append({
                        'model':       'gpt-4',
                        'messages':    [{
                            'role':    'system',
                            'content': str_prompt},
                            {
                            'role':    'user',
                            'content': usr_prompt}]})

        if list_request:
            outputs['request']['ena'] = True
            outputs['request']['ts'].update(timestamp)
            outputs['request']['list'][:] = list_request



