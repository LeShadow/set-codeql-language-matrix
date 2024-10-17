import os
import requests
import json
import sys

token = sys.argv[1]
endpoint = sys.argv[2]
changed_files = sys.argv[3]
exclude = sys.argv[4]
codeql_languages = ["cpp", "csharp", "go", "java", "javascript", "python", "ruby", "typescript", "kotlin", "swift"]
codeql_languages_map = {
    "cpp": [".cpp", ".c++", ".cxx", ".hpp", ".hh", ".h++", ".hxx", ".c", ".cc", ".h"],
    "csharp": [".sln", ".csproj", ".cs", ".cshtml", ".xaml"],
    "go": [".go"],
    "java": [".java", ".kt"],
    "python": [".py"],
    "ruby": [".rb", ".erb", ".gemspec"],
    "swift": [".swift"],
    "typescript": [".ts", ".tsx", ".mts", ".cts"]
    
}

# Connect to the languages API and return languages
def get_languages():
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github.v3+json'}
    response = requests.get(endpoint, headers=headers)
    return response.json()

# Find the intersection of the languages returned by the API and the languages supported by CodeQL
def build_languages_list(languages):
    languages = [language.lower() for language in languages.keys()]
    for i in range(len(languages)):
        if languages[i] == "c#":
            languages[i] = ("csharp")
        if languages[i] == "c++":
            languages[i] = ("cpp")
        if languages[i] == "c":
            languages[i] = ("cpp")
        if languages[i] == "typescript":
            languages[i] = ("javascript")
        if languages[i] == "kotlin":
            languages[i] = ("java")

    intersection = list(set(languages) & set(codeql_languages))
    return intersection

def detect_extensions():
    changed_files_list = changed_files.split(',')
    return {os.path.splitext(f)[1] for f in changed_files_list if os.path.splitext(f)[1]}
    
# return a list of languages based on detected extensions
def detect_languages_from_extensions(set_of_extensions, codeql_languages_map, list_of_languages):
    print(set_of_extensions)
    if not set_of_extensions:
        return list_of_languages
    detected_languages = []
    for language in list_of_languages:
        # Get the extensions for the language from the mapping
        extensions = codeql_languages_map.get(language, [])
        # Check if any of the language's extensions are in the set of extensions
        if set(extensions) & set_of_extensions:
            detected_languages.append(language)
    print(detected_languages)
    return detected_languages

# return a list of objects from language list if they are not in the exclude list
def exclude_languages(language_list):
    excluded = [x.strip() for x in exclude.split(',')]
    output = list(set(language_list).difference(excluded))
    print("languages={}".format(output))
    return output

# Set the output of the action
def set_action_output(output_name, value) :
    if "GITHUB_OUTPUT" in os.environ :
        with open(os.environ["GITHUB_OUTPUT"], "a") as f :
            print("{0}={1}".format(output_name, value), file=f)

def main():
    languages = get_languages()
    language_list = build_languages_list(languages)
    filter_languages_by_extensions = detect_languages_from_extensions(detect_extensions(), codeql_languages_map, language_list)
    output = exclude_languages(filter_languages_by_extensions)
    set_action_output("languages", json.dumps(output))

if __name__ == '__main__':
    main()


