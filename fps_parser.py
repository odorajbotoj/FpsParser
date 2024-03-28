# base on github.com/zhblue/freeproblemset/FPSPythonParser/parser.py
import copy
import base64
import os
import random
import re
import string
import xml.etree.ElementTree as ET


class FPSParser(object):
    def __init__(self, fps_path):
        self.fps_path = fps_path
        self.version = None

    @property
    def _root(self):
        root = ET.ElementTree(file=self.fps_path).getroot()
        self.version = root.attrib.get("version", "No Version")
        if self.version not in ["1.1", "1.2"]:
            raise ValueError("Unsupported version '" + self.version + "'")
        return root

    def parse(self):
        ret = []
        for node in self._root:
            if node.tag == "item":
                ret.append(self._parse_one_problem(node))
        return ret

    def _parse_one_problem(self, node):
        sample_start = True
        test_case_start = True
        problem = {"title": "No Title", "description": "No Description",
                   "input": "No Input Description",
                   "output": "No Output Description",
                   "memory_limit": {"unit": None, "value": None},
                   "time_limit": {"unit": None, "value": None},
                   "samples": [], "images": [], "append": [],
                   "template": [], "prepend": [], "test_cases": [],
                   "hint": None, "source": None, "spj": None, "solution": []}
        for item in node:
            tag = item.tag
            if tag in ["title", "description", "input", "output", "hint", "source"]:
                problem[item.tag] = item.text
            elif tag == "time_limit":
                unit = item.attrib.get("unit", "s")
                if unit not in ["s", "ms"]:
                    raise ValueError("Invalid time limit unit")
                problem["time_limit"]["unit"] = item.attrib.get("unit", "s")
                value = 0
                if self.version != "1.1":
                    value = float(item.text)
                else:
                    value = int(item.text)
                if value <= 0:
                    raise ValueError("Invalid time limit value")
                problem["time_limit"]["value"] = value
            elif tag == "memory_limit":
                unit = item.attrib.get("unit", "MB")
                if unit not in ["MB", "KB", "mb", "kb"]:
                    raise ValueError("Invalid memory limit unit")
                problem["memory_limit"]["unit"] = unit.upper()
                value = int(item.text)
                if value <= 0:
                    raise ValueError("Invalid memory limit value")
                problem["memory_limit"]["value"] = value
            elif tag in ["template", "append", "prepend", "solution"]:
                lang = item.attrib.get("language")
                if not lang:
                    raise ValueError("Invalid " + tag + ", language name is missed")
                problem[tag].append({"language": lang, "code": item.text})
            elif tag == 'spj':
                lang = item.attrib.get("language")
                if not lang:
                    raise ValueError("Invalid spj, language name if missed")
                problem["spj"] = {"language": lang, "code": item.text}
            elif tag == "img":
                problem["images"].append({"src": None, "blob": None})
                for child in item:
                    if child.tag == "src":
                        problem["images"][-1]["src"] = child.text
                    elif child.tag == "base64":
                        problem["images"][-1]["blob"] = child.text
            elif tag == "sample_input":
                if not sample_start:
                    raise ValueError("Invalid xml, error 'sample_input' tag order")
                problem["samples"].append({"input": item.text, "output": None})
                sample_start = False
            elif tag == "sample_output":
                if sample_start:
                    raise ValueError("Invalid xml, error 'sample_output' tag order")
                problem["samples"][-1]["output"] = item.text
                sample_start = True
            elif tag == "test_input":
                if not test_case_start:
                    raise ValueError("Invalid xml, error 'test_input' tag order")
                problem["test_cases"].append({"input": item.text, "output": None})
                test_case_start = False
            elif tag == "test_output":
                if test_case_start:
                    raise ValueError("Invalid xml, error 'test_output' tag order")
                problem["test_cases"][-1]["output"] = item.text
                test_case_start = True

        return problem


class FPSHelper(object):
    def save_image(self, problem, base_dir, base_url=""):
        try:
            os.makedirs(base_dir)
        except FileExistsError:
            pass
        _problem = copy.deepcopy(problem)
        for img in _problem["images"]:
            name = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12))
            ext = os.path.splitext(img["src"])[1]
            file_name = name + ext
            with open(os.path.join(base_dir, file_name), "wb") as f:
                f.write(base64.b64decode(img["blob"]))
            for item in ["description", "input", "output"]:
                _problem[item] = _problem[item].replace(img["src"], os.path.join(base_url, file_name))
        return _problem

    def save_test_case(self, problem, base_dir, input_preprocessor=None, output_preprocessor=None):
        try:
            os.makedirs(base_dir)
        except FileExistsError:
            pass
        for index, item in enumerate(problem["test_cases"]):
            with open(os.path.join(base_dir, get_name_en(problem["title"]) + str(index + 1) + ".in"), "w", encoding="utf-8") as f:
                if input_preprocessor:
                    input_content = input_preprocessor(item["input"])
                else:
                    input_content = item["input"]
                f.write(str(input_content))
            with open(os.path.join(base_dir, get_name_en(problem["title"]) + str(index + 1) + ".out"), "w", encoding="utf-8") as f:
                if output_preprocessor:
                    output_content = output_preprocessor(item["output"])
                else:
                    output_content = item["output"]
                f.write(str(output_content))
    
    def save_problem(self, problem, base_dir):
        try:
            os.makedirs(base_dir)
        except FileExistsError:
            pass
        with open(os.path.join(base_dir, str(problem["title"]) + ".html"), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE HTML><h1>"+str(problem["title"])+"</h1><hr/>")
            f.write("<h2>题目描述</h2><fieldset>"+str(problem["description"])+"</fieldset>")
            f.write("<h2>输入描述</h2><fieldset>"+str(problem["input"])+"</fieldset>")
            f.write("<h2>输出描述</h2><fieldset>"+str(problem["output"])+"</fieldset>")
            f.write("<h2>时间限制</h2><fieldset>"+str(problem["time_limit"]["value"])+str(problem["time_limit"]["unit"])+"</fieldset>")
            f.write("<h2>空间限制</h2><fieldset>"+str(problem["memory_limit"]["value"])+str(problem["memory_limit"]["unit"])+"</fieldset>")
            f.write("<h2>样例</h2><fieldset>")
            for index, item in enumerate(problem["samples"]):
                f.write("<fieldset><legend>样例"+str(index+1)+"</legend><h3>输入</h3><fieldset><pre>"+str(item["input"])+"</pre></fieldset><h3>输出</h3><fieldset><pre>"+str(item["output"])+"</pre></fieldset></fieldset>")
            f.write("</fieldset>")
            f.write("<h2>提示</h2><fieldset>"+str(problem["hint"])+"</fieldset>")
            f.write("<h2>来源</h2><fieldset>"+str(problem["source"])+"</fieldset>")
            if len(problem["template"]) != 0:
                f.write("<h2>程序样板</h2><fieldset>")
                for item in problem["template"]:
                    f.write("<fieldset><legend>"+str(item["language"])+"</legend><pre>"+str(item["code"])+"</pre></fieldset>")
                f.write("</fieldset>")
            if len(problem["prepend"]) != 0:
                f.write("<h2>自动前缀</h2><fieldset>")
                for item in problem["prepend"]:
                    f.write("<fieldset><legend>"+str(item["language"])+"</legend><pre>"+str(item["code"])+"</pre></fieldset>")
                f.write("</fieldset>")
            if len(problem["append"]) != 0:
                f.write("<h2>自动后缀</h2><fieldset>")
                for item in problem["append"]:
                    f.write("<fieldset><legend>"+str(item["language"])+"</legend><pre>"+str(item["code"])+"</pre></fieldset>")
                f.write("</fieldset>")

    def save_spj(self, problem, base_dir):
        try:
            os.makedirs(base_dir)
        except FileExistsError:
            pass
        with open(os.path.join(base_dir, str(problem["title"]) + "-spj.html"), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE HTML><h1>"+str(problem["title"])+"</h1><hr/>")
            if problem["spj"] != None:
                f.write("<h2>SPJ</h2><fieldset><fieldset><legend>"+str(problem["spj"]["language"])+"</legend><pre>"+str(problem["spj"]["code"])+"</pre></fieldset></fieldset>")
    
    def save_solution(self, problem, base_dir):
        try:
            os.makedirs(base_dir)
        except FileExistsError:
            pass
        with open(os.path.join(base_dir, str(problem["title"]) + "-solution.html"), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE HTML><h1>"+str(problem["title"])+"</h1><hr/>")
            if len(problem["solution"]) != 0:
                f.write("<h2>题解</h2><fieldset>")
                for item in problem["solution"]:
                    f.write("<fieldset><legend>"+str(item["language"])+"</legend><pre>"+str(item["code"])+"</pre></fieldset>")
                f.write("</fieldset>")


def get_name_en(s):
    r = re.search(r"(?<=\(|（)(.+?)(?=\)|）)", s)
    if r != None:
        return r.group()
    return ""


if __name__ == "__main__":
    for fps_file in os.listdir("."):
        if fps_file.split(".")[-1] == "xml":
            try:
                parser = FPSParser(fps_file)
                helper = FPSHelper()
                problems = parser.parse()
                for problem in problems:
                    path = os.path.join("output", problem["title"])
                    helper.save_test_case(problem, os.path.join(path, "data"))
                    helper.save_spj(problem, path)
                    helper.save_solution(problem, path)
                    problem = helper.save_image(problem, path)
                    helper.save_problem(problem, path)
            except Exception as e:
                print("err: "+fps_file)
                print(e)
                #raise e

    