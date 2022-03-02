from langdetect import detect_langs



print(detect_langs("ciao sono qui"))

print(detect_langs("ciao sono qui",profiles_directory='timed_profiles'))
