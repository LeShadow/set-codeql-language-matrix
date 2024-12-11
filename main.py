import os
import requests
import json
import sys
from githubkit import GitHub, Response
from githubkit.versions.latest.models import FullRepository, DiffEntry

token = sys.argv[1]
repository_info = sys.argv[2]
changed_file_option = json.loads(sys.argv[3].strip().lower())
pr_number = sys.argv[4]
exclude = sys.argv[5]

codeql_languages = ["cpp", "csharp", "go", "java", "javascript", "python", "ruby", "typescript", "kotlin", "swift"]
codeql_languages_map = {
    "cpp": [".cpp", ".c++", ".cxx", ".hpp", ".hh", ".h++", ".hxx", ".c", ".cc", ".h"],
    "csharp": [".sln", ".csproj", ".cs", ".cshtml", ".xaml"],
    "go": [".go"],
    "java": [".java", ".kt"],
    "python": [".py"],
    "ruby": [".rb", ".erb", ".gemspec"],
    "swift": [".swift"],
    "javascript": [".ts", ".tsx", ".mts", ".cts",".js",".jsx",".mjs",".es",".es6",".htm",".html",".xhtm",".xhtml",".vue",".hbs",".ejs",".njk",".json",".yaml",".yml",".raml",".xml"]
    
}
changed_files = []

GithubClient = GitHub(token)

# Connect to the languages API and return languages
def get_languages():
    resp: Response[FullRepository] = GithubClient.rest.repos.list_languages(repository_info.split('/')[0],
                                                                            repository_info.split('/')[1])
    return resp.json()

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

def get_changed_files():
    for changed_file in GithubClient.paginate(GithubClient.rest.pulls.list_files, owner=repository_info.split('/')[0], repo=repository_info.split('/')[1], pull_number=pr_number):
        changed_file: DiffEntry
        if changed_file.status != "removed":
            changed_files.append(changed_file.filename)

# Get a list of extensions from the list of files 
def detect_extensions():
    get_changed_files()
    #changed_files_list = changed_files.split(',')
    return {os.path.splitext(f)[1] for f in changed_files if os.path.splitext(f)[1]}
    
# return a list of languages based on detected extensions
def detect_languages_from_extensions(set_of_extensions, codeql_languages_map, list_of_languages):
    if not set_of_extensions:
        return list_of_languages
    detected_languages = []
    for language in list_of_languages:
        # Get the extensions for the language from the mapping
        extensions = codeql_languages_map.get(language, [])
        # Check if any of the language's extensions are in the set of extensions
        if set(extensions) & set_of_extensions:
            detected_languages.append(language)
    # Now, find if there's any extension that belongs to a language *not* in the list_of_languages
    # and that language isn't already detected.
    all_languages = set(codeql_languages_map.keys())
    known_languages = set(list_of_languages)
    unknown_languages = all_languages - known_languages

    for language in unknown_languages:
        extensions = codeql_languages_map.get(language, [])
        if set(extensions) & set_of_extensions:
            if language not in detected_languages:
                detected_languages.append(language)
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
    if changed_file_option:
        language_list = detect_languages_from_extensions(detect_extensions(), codeql_languages_map, language_list)
    output = exclude_languages(language_list)
    set_action_output("languages", json.dumps(output))

if __name__ == '__main__':
    main()


