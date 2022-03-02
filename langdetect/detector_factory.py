import os
from os import path
import sys
from datetime import datetime

try:
    import simplejson as json
except ImportError:
    import json

from .detector import Detector
from .lang_detect_exception import ErrorCode, LangDetectException
from .utils.lang_profile import LangProfile


class DetectorFactory(object):
    '''
    Language Detector Factory Class.

    This class manages an initialization and constructions of Detector.

    Before using language detection library,
    load profiles with DetectorFactory.load_profile(str)
    and set initialization parameters.

    When the language detection,
    construct Detector instance via DetectorFactory.create().
    See also Detector's sample code.
    '''
    seed = None
    expiration_day = None

    def __init__(self):
        self.word_lang_prob_map = {}
        self.langlist = []

    def get_expiration_day(self):
        return self.expiration_day

    def set_expiration_day(self, expiration):
        self.expiration_day = expiration

    def get_best_timehash(self, options: list[str]) -> str:
        current_datetime = datetime.now().strftime("%m%d%Y%H%M")
        int_sorted_timehash = sorted([int(x) for x in options], reverse=True)

        for timestamps in int_sorted_timehash:
            if timestamps <= int(current_datetime):
                if len(str(timestamps)) < 12:
                    return f"0{str(timestamps)}"
                return str(timestamps)

        raise NameError('No timehash directory fit requirements')

    def load_profile(self, profile_directory, mode='classic'):
        if mode == 'classic':
            list_files = os.listdir(profile_directory)
        else:
            timehash_dirs = os.listdir(profile_directory)
            profile_directory = path.join(profile_directory, self.get_best_timehash(timehash_dirs))
            print(f"-- using {profile_directory} dictionaries")  # for debug
            list_files = os.listdir(profile_directory)
        if not list_files:
            raise LangDetectException(ErrorCode.NeedLoadProfileError, 'Not found profile: ' + profile_directory)

        langsize, index = len(list_files), 0
        for filename in list_files:
            if filename.startswith('.'):
                continue
            filename = path.join(profile_directory, filename)
            if not path.isfile(filename):
                continue

            f = None
            try:
                if sys.version_info[0] < 3:
                    f = open(filename, 'r')
                else:
                    f = open(filename, 'r', encoding='utf-8')
                json_data = json.load(f)
                profile = LangProfile(**json_data)
                self.add_profile(profile, index, langsize)
                index += 1
            except IOError:
                raise LangDetectException(ErrorCode.FileLoadError, 'Cannot open "%s"' % filename)
            except:
                raise LangDetectException(ErrorCode.FormatError, 'Profile format error in "%s"' % filename)
            finally:
                if f:
                    f.close()

    def load_json_profile(self, json_profiles):
        langsize, index = len(json_profiles), 0
        if langsize < 2:
            raise LangDetectException(ErrorCode.NeedLoadProfileError, 'Need more than 2 profiles.')

        for json_profile in json_profiles:
            try:
                json_data = json.loads(json_profile)
                profile = LangProfile(**json_data)
                self.add_profile(profile, index, langsize)
                index += 1
            except:
                raise LangDetectException(ErrorCode.FormatError, 'Profile format error.')

    def add_profile(self, profile, index, langsize):
        lang = profile.name
        if lang in self.langlist:
            raise LangDetectException(ErrorCode.DuplicateLangError, 'Duplicate the same language profile.')
        self.langlist.append(lang)

        for word in profile.freq:
            if word not in self.word_lang_prob_map:
                self.word_lang_prob_map[word] = [0.0] * langsize
            length = len(word)
            if 1 <= length <= 3:
                prob = 1.0 * profile.freq.get(word) / profile.n_words[length - 1]
                self.word_lang_prob_map[word][index] = prob

    def clear(self):
        self.langlist = []
        self.word_lang_prob_map = {}

    def create(self, alpha=None):
        '''Construct Detector instance with smoothing parameter.'''
        detector = self._create_detector()
        if alpha is not None:
            detector.set_alpha(alpha)
        return detector

    def _create_detector(self):
        if not self.langlist:
            raise LangDetectException(ErrorCode.NeedLoadProfileError, 'Need to load profiles.')
        return Detector(self)

    def set_seed(self, seed):
        self.seed = seed

    def get_lang_list(self):
        return list(self.langlist)


PROFILES_DIRECTORY = path.join(path.dirname(__file__), 'profiles')
_factory = None


def init_factory(profiles_directory: str):
    global _factory
    if _factory is None:
        _factory = DetectorFactory()
        _factory.load_profile(path.join(path.dirname(__file__), profiles_directory), mode='classic')
    elif profiles_directory.find('timed_') == 0:
        _factory = DetectorFactory()
        _factory.load_profile(path.join(path.dirname(__file__), profiles_directory), mode='expiration')


def detect(text: str, profiles_directory='profiles'):
    init_factory(profiles_directory)
    detector = _factory.create()
    detector.append(text)
    return detector.detect()


def detect_langs(text: str, profiles_directory='profiles'):
    init_factory(profiles_directory)
    detector = _factory.create()
    detector.append(text)
    return detector.get_probabilities()
