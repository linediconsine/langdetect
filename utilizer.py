from langdetect import detect_langs




## check timed_profiles working
print(detect_langs("ciao sono qui",profiles_directory='timed_profiles'))

## check cache
print(detect_langs("ciao sono qui",profiles_directory='timed_profiles'))

# Normal usage
print(detect_langs("ciao sono qui"))