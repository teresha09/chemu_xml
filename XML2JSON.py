import os
import argparse
import xml.etree.ElementTree as ET
import pandas as pd


parser = argparse.ArgumentParser()
parser.add_argument("-data", "--data", type=str, default='applications') ##  путь до папки с xml
parser.add_argument("-out", "--out", type=str, default='train') ## train or test
parser.add_argument("-files", "--files", type=int, default=50) ## количество файлов
args = parser.parse_args()


def file_loop(num):
    """

    :param num: количество файлов для обработки
    :return: лист, какждый элемент которого один reaction с текстом и сущностями
    """
    counter = 0
    index = 0
    result_list = []
    for folder in os.listdir(args.data):
        folder_path = os.path.join(args.data, folder)
        for f in os.listdir(folder_path):
            if counter > num:
                break
            xml_file = os.path.join(folder_path, f)
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for reaction in root:
                if counter > num:
                    break
                result_list.append(parse_reaction(reaction, index))
                index += 1
                counter += 1
    return result_list


def parse_reaction(reaction, index):
    """

    :param reaction: элемент XML дерева
    :param index:
    :return: словарь для одного reaction с текстом и сущностями
    """
    s = ""
    reaction_product = []
    percenty_yield = []
    other_yield = []
    other_compound = []
    solvent = []
    catalyst = []
    time = []
    temperature = []
    ent_list = []
    for i in reaction[0]:
        if i.tag.find("paragraphText") != -1 or i.tag.find("headingText") != -1:
            s += i.text + " "
    for i in range(len(reaction[2])):
        if reaction[2][i][0][0].text != "title compound":
            reaction_product.append([reaction[2][i][0][0].text])
        elif len(reaction[2][i][0]) > 1:
            reaction_product.append([reaction[2][i][0][1].text])
        for j in reaction[2][i]:
            if j.tag.find("amount") != -1:
                for key in j.attrib:
                    if j.attrib[key] == 'PERCENTYIELD':
                        percenty_yield.append([j.text])
                        break
                    elif j.attrib[key] == 'CALCULATEDPERCENTYIELD':
                        break
                    else:
                        other_yield.append([j.text])
                        break

    for i in range(len(reaction[3])):
        other_compound.append([reaction[3][i][0][0].text])
        for j in reaction[3][i]:
            if j.tag.find("amount") != -1:
                for key in j.attrib:
                    if j.attrib[key] == 'PERCENTYIELD':
                        percenty_yield.append([j.text])
                        break
                    elif j.attrib[key] == 'CALCULATEDPERCENTYIELD':
                        break
                    else:
                        other_yield.append([j.text])
                        break

    for i in range(len(reaction[4])):
        solvent_flag = False
        catalyst_flag = False
        for key in reaction[4][i].attrib:
            if reaction[4][i].attrib[key].find("solvent") != -1:
                solvent_flag = True
                break
            if reaction[4][i].attrib[key].find("catalyst") != -1:
                catalyst_flag = True
                break
        if solvent_flag:
            solvent.append([reaction[4][i][0][0].text])
        if catalyst_flag:
            catalyst.append([reaction[4][i][0][0].text])

    for i in range(len(reaction[5])):
        for j in range(len(reaction[5][i])):
            if reaction[5][i][j].tag.find("parameter") != -1:
                for key in reaction[5][i][j].attrib:
                    if reaction[5][i][j].attrib[key] == "Time":
                        time.append([reaction[5][i][j].text])
                        break
                    if reaction[5][i][j].attrib[key] == "Temperature":
                        temperature.append([reaction[5][i][j].text])
            if reaction[5][i][j].tag.find("atmosphere") != -1:
                other_compound.append([reaction[5][i][j][0][0][0].text])

    for i in range(len(reaction_product)):
        reaction_product[i] = positions(reaction_product[i], s)
        reaction_product[i].append('reaction_product')
        ent_list.append(reaction_product[i])
    for i in range(len(percenty_yield)):
        percenty_yield[i] = positions(percenty_yield[i], s)
        percenty_yield[i].append("percent_yield")
        ent_list.append(percenty_yield[i])
    for i in range(len(other_yield)):
        other_yield[i] = positions(other_yield[i], s)
        other_yield[i].append("other_yield")
        ent_list.append(other_yield[i])
    for i in range(len(other_compound)):
        other_compound[i] = positions(other_compound[i], s)
        other_compound[i].append("other_compound")
        ent_list.append(other_compound[i])
    for i in range(len(solvent)):
        solvent[i] = positions(solvent[i], s)
        solvent[i].append("solvent")
        ent_list.append(solvent[i])
    for i in range(len(catalyst)):
        catalyst[i] = positions(catalyst[i], s)
        catalyst[i].append("catalyst")
        ent_list.append(catalyst[i])
    for i in range(len(time)):
        time[i] = positions(time[i], s)
        time[i].append("time")
        ent_list.append(time[i])
    for i in range(len(temperature)):
        temperature[i] = positions(temperature[i], s)
        temperature[i].append("temperature")
        ent_list.append(temperature[i])

    ent_dict = {}
    for i in range(len(ent_list)):
        if len(ent_list) < 4:
            print("hello")
        if ent_list[i][1] == -1 or ent_list[i][2] == -1:
            continue
        ent_dict[i] = {"start": ent_list[i][1], "end": ent_list[i][2],
                       "entity": ent_list[i][3], "text": ent_list[i][0]}
    result_dict = {"index": index,"text": s, "entities": ent_dict}
    return result_dict


def positions(ent, text):
    """
    находим позицию сущности в тексте
    :param ent:
    :param text:
    :return:
    """
    ent.append(text.find(ent[0]))
    ent.append(ent[1] + len(ent[0]))
    return ent


res = file_loop(50)
df = pd.DataFrame(columns=['text', 'entities'])
for i in range(len(res)):
    df = df.append({'text':res[i]["text"], "entities": res[i]["entities"]},
                   ignore_index=True)

df.to_json("{}.json", orient="table")

