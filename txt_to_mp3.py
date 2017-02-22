#!/usr/bin/env python
from argparse import ArgumentParser
import subprocess
from boto3 import Session
from botocore.exceptions import ClientError

session = Session(profile_name="personal")
polly = session.client("polly")


def load_textfile(path):
    with open(path) as f:
        return f.readlines()


def convert_text(input_text):
    """Takes input_text, returns object with audo stream
    https://boto3.readthedocs.io/en/latest/reference/services/polly.html#Polly.Client.synthesize_speech

    Response Structure
    (dict) {AudioStream (StreamingBody),..}
    """
    def _divide_input(input_text):
        return input_text.split('.')

    def _synth_speech(input_text):
        return polly.synthesize_speech(
            OutputFormat='mp3',
            # SampleRate='string',
            Text=input_text,
            TextType='text',
            VoiceId='Joanna'
        )
    try:
        response = _synth_speech(input_text)
    except ClientError as e:
        print e
        print 'Input text length: ', len(input_text)
        print input_text
        # TODO: handle split and combine correctly
        # print 'Trying to split...'
        # sentences = _divide_input(input_text)
        # for sentence in sentences:
        #     response = _synth_speech

    return response['AudioStream']


def write_current_text(input_text, idx, debug=True):
    if debug:
        print input_text

    response_stream = convert_text(input_text)

    with open('tmpoutput_%s' % idx, 'w') as f:
        f.write(response_stream.read())


def combine_outputs(output_name):
    """List the output files in numerical order,
    and combine them into one using cat"""
    cat_command = 'cat $(ls tmpoutput_* | sort -n -t "_" -k 2) > "%s"' % output_name.replace("'", '')
    subprocess.check_call(cat_command, shell=True)

    # Cleanup the tmp files
    rm_command = 'rm -f ./tmpoutput_*'
    subprocess.check_call(rm_command, shell=True)


def main(args):

    full_text = load_textfile(args.path)

    current_conversion_text = ''
    idx = 0
    while True:
        try:
            next_text = full_text[idx]
        except IndexError:
            print 'Done!'
            break

        if len(current_conversion_text) + len(next_text) > 1500:
            # If the combination would be too big, write first,
            # then have the next iteration start with next_text
            write_current_text(current_conversion_text, idx, args.debug)
            current_conversion_text = next_text
        else:
            # If the addition is small enough, synth them in one request
            current_conversion_text += next_text
            write_current_text(current_conversion_text, idx, args.debug)
            current_conversion_text = ''

        idx += 1

    # Don't forget the final leftovers
    if current_conversion_text:
        write_current_text(current_conversion_text, idx, args.debug)

    output_name = args.path.replace('.txt', '.mp3')
    print 'Output file:', output_name
    combine_outputs(output_name)

if __name__ == '__main__':
    cli = ArgumentParser(description='Example conversion of text file to mp3 file')
    cli.add_argument("--path", type=str, default="nytimes_ai.txt")
    cli.add_argument("--debug", action="store_true", default=False)
    arguments = cli.parse_args()
    main(arguments)
