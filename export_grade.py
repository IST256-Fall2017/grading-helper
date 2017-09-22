#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv

class GradeExporter():
    _folder_list = []

    # list of lists
    # ex: ((netid, githubun), (netid2, githubun2))
    _student_netids = []

    _grades = []
    _basepath = None
    _export_filename = None

    def __init__(self, basepath, filename):
        self._basepath = basepath
        self._export_filename = filename

    def _load_students(self):
        print("Loading students from file")
        with open(os.path.join(self._basepath, "students.csv"), 'r') as file:
            for line in file:
                if line != "\n":
                    data = line.split(",")
                    self._student_netids.append((data[0].strip(), data[1].strip()))


    def _load_folders(self):
        print("Loading folder list")
        self._folder_list = os.listdir(self._basepath)

    def _get_grade_from_file(self, filepath):
        print("Loading grade from {}".format(filepath))
        try:
            with open(filepath, 'r') as file:
                for line in file:
                    if "Total Grade" in line:
                        try:
                            grade = line.split(":")[1]
                            grade = grade.strip()
                            return int(grade)
                        except IndexError:
                            print("ERROR: No Grade found")
                            return 0
                        except TypeError:
                            print("ERROR: Grade isn't an integer")
                            return 0
        except FileNotFoundError:
            print("ERROR: GRADE.md not found")
            return 0

    def _get_folder_from_netid(self, ghuser):
        for folder in self._folder_list:
            if ghuser in folder:
                return folder
        print("ERROR: folder not found")
        raise FileNotFoundError()

    def _load_grades(self):
        print("Loading Grades")
        for student in self._student_netids:
            print("Getting grade for {}".format(student[0]))
            try:
                folder = self._get_folder_from_netid(student[1])
                file_path = os.path.join(self._basepath, folder, "GRADE.md")
                grade = self._get_grade_from_file(file_path)
                self._grades.append((student[0], grade))
            except FileNotFoundError:
                print("ERROR: Could not grade {}".format(student[0]))
                self._grades.append((student[0], "NA"))

    def _write_to_csv(self):
        print("Writing grades to {}".format(self._export_filename))
        with open(os.path.join(self._basepath, self._export_filename), 'w', newline='') as csvfile:
            gradefilewriter = csv.writer(csvfile)
            for grade in self._grades:
                gradefilewriter.writerow(grade)
            

    def get_grades(self):
        self._load_students()
        self._load_folders()
        self._load_grades()
        self._write_to_csv()
        return self._grades