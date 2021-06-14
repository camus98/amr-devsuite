import json, sys, time, os
import pandas as pd
from basics import *
from standard import *
from correlation import *
import amr_diff
from style import HTML_AMR


def print_testcase(sents, amrs, h_score, metrics, expl, sick=True):

	string = []
	for i, sent in enumerate(sents):
		if len(sent.split()) > 10 and len(sent.split()) > 11:
			splitted = sent.split()
			sents[i] = [" ".join(splitted[:9]), " ".join(splitted[9:])]
		else:
			sents[i] = [sents[i]]
	if expl:
		string.append('{}\n\n'.format(expl))
	sents = balance_len(sents)
	for i, sent in enumerate(sents[0]):
		string.append('{0:50}  {1}\n'.format(sent, sents[1][i]))
	string[-1] += "\n"

	amrs = balance_len(amrs)
	for i, line in enumerate(amrs[0]):
		if not line.startswith("# ::snt"):
			string.append('{0:50}  {1}\n'.format(line.strip("\n"), amrs[1][i].strip("\n")))
	string.append("\n")

	string.append("Scores:\n-------\n")
	if sick:
		string.append('{0:30}  {1} ({2})\n\n'.format("Semantic Relatedness Score:", str(h_score), round(norm(h_score, "sick"), 3)))
	else:
		string.append('{0:30}  {1} ({2})\n\n'.format("Semantic Similarity Score:", str(h_score), round(norm(h_score, "sts"), 3)))

	mets = [(k, str(round(v, 3))) if isinstance(v, float) else (k, v) for k,v in metrics.items()]
	mets.sort(key=lambda x:x[0])

	for met in mets:	
		string.append('{0:15} ---  {1}\n'.format(met[0], str(met[1])))
	string.append("\n---------------------------------------------------------------------------------------------------\n")
	return string


def write_html(amrs, h_score, metrics, sick=True):

	tmp1, tmp2 = make_tmp(amrs)

	# tmp1, tmp2 = "/home/laura/Dokumente/CoLi/BA/AMR_ex/peel.amr", "/home/laura/Dokumente/CoLi/BA/AMR_ex/slice.amr"

	try:
		html_out = amr_diff.main(tmp1, tmp2)
	except (IndexError, KeyError):
		return ""

	html = html_out.split("\n")

	string = "\n".join(html[44:-6])
	# string = html[:-6]

	string += '<br><h4>Scores:</h4>\n'
	if sick:
		string += 'Semantic Relatedness Score: {} ({})<br><br>\n'.format(str(h_score), round(norm(h_score, "sick"), 3))
	else:
		string += 'Semantic Similarity Score: {} ({})<br><br>\n'.format(str(h_score), round(norm(h_score, "sts"), 3))

	# print(metrics)
	mets = [(k, str(round(v, 3))) if isinstance(v, float) else (k, v) for k,v in metrics.items()]
	mets.sort(key=lambda x:x[0])

	string += '<table style="width:30%">'
	for met in mets:	
		string += '<tr><td>{}</td><td>{}</td><tr>'.format(met[0], str(met[1]))
	string += '</table></p>\n'
	string += '<hr style="width:50%;text-align:left;margin-left:0">\n'

	return string


def compute_av_scores(id_list, metrics, tested, metric_dict):

	compute, average = {}, {}
	wanted = metrics + tested

	for idx in id_list:
		# if not [v for k, v in metric_dict[idx].items() if k in wanted and np.isnan(v)]:
		for key, value in metric_dict[idx].items():
			if key in metrics or key == "Ann. Score" or key in tested:
				try:
					compute[key].append(value)
				except KeyError:
					compute[key] = [value]

	for metric, scores in compute.items():
		average[metric] = np.mean(np.array([score for score in scores if not isinstance(score, str) and not np.isnan(score)]))

	return compute, average


def norm(value, ss):
	if ss == "sick":
		return (value - 1) / (5 - 1)
	else:
		return value / 5


def balance_len(vals):
	if len(vals[0]) < len(vals[1]):
		vals[0].extend(["\n\n"]*(len(vals[1]) - len(vals[0])))
	elif len(vals[0]) > len(vals[1]):
		vals[1].extend(["\n\n"]*(len(vals[0]) - len(vals[1])))

	return vals


if __name__ == "__main__":

	m_lines = read_file("../metrics.txt")
	wanted = [line.strip() for line in m_lines if line and not line.startswith("#")]
	# print(wanted)
	# exit()
	y_lines = read_file("../my_metrics.txt")
	your_wanted = [line.strip() for line in y_lines if line and not line.startswith("#")]

	all_used_ids = {"sick": [], "sts": []}

	test_cases = read_json("../data/ids_test_cases.json")
	vals = read_json("../data/content_test_cases.json")
	def_metric_dict = read_json("../data/metric_scores.json")
	# your_scores = read_json("/home/laura/ba_thesis/metric_scores_LCG.json")

	try:
		if sys.argv[1] == '-m':
			your_scores = {}
			your_wanted = []
		else:
			try:
				your_scores = read_json(sys.argv[1])
			except FileNotFoundError:
				print("Your file could not be found, please check the path!")
	except IndexError:
		print("Please provide the path to your metrics or add the flag '-m' if you don't have a metric to test.")
		exit()
	try:
		if sys.argv[2] == "-html":
			html = True
	except IndexError:
		html = False

	metric_dict = {}
	for k,v in def_metric_dict.items():
		metric_dict[k] = v

	if your_scores:
		for k,v in your_scores.items():
			for met in v:
				metric_dict[k][met] = your_scores[k][met]


	print("\n------------------------------------------\nOVERVIEW\n------------------------------------------\n\n")
	print("Number of Test Cases by Phenomenon:\n")
	create_table_nums(test_cases)
	print("\n\nSICK Data Set\n\n")
	print("The Test Cases from the SICK Data Set were annotated with a Semantic Relatedness Score.\nThe score ranges from 1 (completely unrelated) to 5 (very related).\n\nSemantic Relatedness Score (SR) Statistics:\n")
	create_table_comps(test_cases, vals, "sick")
	print("\n\nSTS Data Set\n\n")
	print("The Test Cases from the SICK Data Set were annotated with a Semantic Similarity Score.\nThe score ranges from 0 (on different topics) to 5 (completely equivalent).\n\nSemantic Similarity Score (SS) Statistics:\n")
	create_table_comps(test_cases, vals, "sts")
	print("\n\nEvaluating Test Cases...\n\n---------------------------------------------------------\n")
	all_average_sick, av_columns_sick = {}, []
	all_average, av_columns = {}, []
	corr_hj_sick, corr_hj = {}, {}
	for phenomenon in sorted(test_cases.keys()):
		# if phenomenon != "Multiple Phenomena":
		pp = ["-" for i in range(len(phenomenon) + 10)]
		# print("{}\n     {}\n{}\n".format("".join(pp), phenomenon, "".join(pp)))
		if html:
			phen_file = '<!DOCTYPE html>\n<html>\n<style>\n'
			phen_file += HTML_AMR.style_sheet()
			phen_file += '</style>\n\n<body style="font-family: Helvetica">\n'
			phen_file += '<h1>{}</h1>\n'.format(phenomenon)
			for ss, sub_phens in test_cases[phenomenon].items():
				phen_file += '<h2>{} Data Set</h2>\n'.format(ss.upper())
				all_ids = [idx for k,v in sub_phens.items() for idx in v]
				correlation, average = compute_av_scores(all_ids, wanted, your_wanted, metric_dict)
				matrix = frame(correlation)			
				if ss == "sick":
					s = "Relatedness"
					rel = True
				else:
					s = "Similarity"
					rel = False	
				id_list = [x for phen, ids in sub_phens.items() for x in ids]
				total = [vals[idx][0] for idx in id_list]
				phen_file += '<h2>Number of Test Cases: {}</h2>'.format(len(id_list))
				phen_file += '<h2>Semantic {} Statistics:</h2>'.format(s)
				normed = [norm(tot, ss) for tot in total]
				columns = [("Mean:", round(compute_mean(total), 2), round(compute_mean(normed), 2)), ("Median:", round(compute_median(total), 2), round(compute_median(normed), 2)), ("Standard deviation:", round(compute_stan_deviation(total), 2), round(compute_stan_deviation(normed), 2)), ("Standard Error:", round(compute_stan_error(total), 2), round(compute_stan_error(normed), 2))]
				phen_file += '<table style="width:15%">'
				for col in columns:
					phen_file += '<tr><td>{}</td><td>{} ({})</td><tr>'.format(col[0], col[1], col[2])
				phen_file += '</table>\n'
				phen_file += "<br>"
				phen_file += '<h2>Average Scores (Overall):</h2>'
				phen_file += '<h3>Average Semantic {}: {} ({})</h3>'.format(s, round(float(average["Ann. Score"]), 3), round(float(norm(average["Ann. Score"], ss)), 3))
				for met in your_wanted:
					phen_file += '<h3>Tested Score ({}): {}</h3>'.format(met, round(float(average[met]), 3))
				phen_file += '<table style="width:20%">'
				for metric in sorted(average.keys()):
					if metric in wanted:
						phen_file += '<tr><td>{}</td><td>{}</td><tr>'.format(metric, round(float(average[metric]), 3))
				phen_file += '</table>\n'
				phen_file += '<h2>Correlation Matrix (Overall):</h2>\n'
				phen_file += matrix.to_html()
				phen_file += '\n<br><hr>\n'
				for phen in sorted(sub_phens.keys()) :
					if len(sub_phens.keys()) > 1:
						phen_ids = [idx for idx in sub_phens[phen]]
						all_used_ids[ss].extend(phen_ids)
						corr_phen, av_phen = compute_av_scores(phen_ids, wanted, your_wanted, metric_dict)
						matrix_phen = frame(corr_phen)
						# create_table_subnums(test_cases, phenomenon, ss)
						phen_file += '<h2>{}</h2>\n<h3>Average Scores:</h3>'.format(phen)
						phen_file += '<h4>Average Semantic {}:   {} ({})</h4>'.format(s, round(float(av_phen["Ann. Score"]), 3), round(float(norm(av_phen["Ann. Score"], ss)), 3))
						for met in your_wanted:
							phen_file += '<h3>Tested Score ({}): {}</h3>'.format(met, round(float(av_phen[met]), 3))
						phen_file += '<table style="width:30%">'
						for metric in sorted(av_phen.keys()):
							if metric in wanted:
								phen_file += '<table style="width:100%"><tr><td>{}</td><td>{}</td><tr></table>'.format(metric, round(float(av_phen[metric]), 3))
						phen_file += '</table>\n'
						phen_file += '<h3>Correlation Matrix:</h3>'
						phen_file += matrix_phen.to_html()
					phen_file += '<br><h3>Scores for Individual Test Cases:</h3>\n<hr style="width:50%;text-align:left;margin-left:0">\n'
					for idx in sub_phens[phen]:
						phen_file += '<h4>{}</h4>'.format(idx)
						phen_file += write_html(vals[idx][2], vals[idx][0], {k:v for k,v in metric_dict[idx].items() if k in wanted or k in your_wanted}, rel)
					phen_file += '<hr>\n'
				# print("{} Data\n=========\n".format(ss.upper()))
				# print("Semantic {} Statistics:\n--------------------------------".format(s))
				# print("\nMean: {:>20}".format(str(round(compute_mean(total), 2))))
				# print("Median: {:>18}".format(str(round(compute_median(total), 2))))
				# print("Standard deviation: {:>6}".format(str(round(compute_stan_deviation(total), 2))))
				# print("Standard error: {:>10}\n\n".format(str(round(compute_stan_error(total), 2))))
				# print("Average Scores:\n---------------\n")
				# print("Average Semantic {}: {} ({})\n".format(s, round(float(average["Ann. Score"]), 3), round(float(norm(average["Ann. Score"], ss)), 3)))
				# for metric in sorted(average.keys()):
					# if metric in wanted:
						# print("{0:15} --   {1}".format(metric, round(float(average[metric]), 3)))
				# print(create_table_scores(sorted(average.keys()), [average[metric] for metric in sorted(average.keys())]))
				# print("\n\nCorrelation Matrix:\n-------------------\n")
				# print(tabulate(matrix, headers='keys', tablefmt='grid'))
				# print(matrix.to_string())
				# print("\n")
			phen_file  += '</body>\n</html>\n'
			with open("../Results_HTML/{}.html".format(phenomenon), 'w+', encoding='utf8') as f:
				f.write(phen_file)
		else:
			php = ["-" for i in range(len(phenomenon) + 10)]
			phen_file = ["{}\n     {}\n{}\n\n".format("".join(php), phenomenon, "".join(php))]
			for ss, sub_phens in test_cases[phenomenon].items():
				all_ids = [idx for k,v in sub_phens.items() for idx in v]
				correlation, average = compute_av_scores(all_ids, wanted, your_wanted, metric_dict)
				matrix = frame(correlation)
				both = wanted + your_wanted
				if ss == "sick":
					s = "Relatedness"
					rel = True
					av_columns_sick.append(phenomenon)
					for met in both:
						if met in all_average_sick:
							all_average_sick[met].append(round(float(average[met.strip()]), 3))
						else:
							all_average_sick[met] = [round(float(average[met.strip()]), 3)]

					unstack = matrix.unstack()
					for k,v in unstack["Ann. Score"].items():
						try:
							corr_hj_sick[k].append(v)
						except KeyError:
							corr_hj_sick[k] = [v]
				else:
					s = "Similarity"
					rel = False
					av_columns.append(phenomenon)
					for met in both:
						if met in all_average:
							all_average[met].append(round(float(average[met.strip()]), 3))
						else:
							all_average[met] = [round(float(average[met.strip()]), 3)]

					unstack = matrix.unstack()
					for k,v in unstack["Ann. Score"].items():
						try:
							corr_hj[k].append(v)
						except KeyError:
							corr_hj[k] = [v]
				id_list = [x for phen, ids in sub_phens.items() for x in ids]
				total = [vals[idx][0] for idx in id_list]
				phen_file.append("{} Data Set\n=============\n\n".format(ss.upper()))
				phen_file.append("Number of Test Cases: {}\n---------------------\n\n".format(len(id_list)))
				phen_file.append("Semantic {} Statistics:\n--------------------------------\n".format(s))
				normed = [norm(tot, ss) for tot in total]
				phen_file.append("Mean: {:>20} ({})".format(str(round(compute_mean(total), 2)), str(round(compute_mean(normed), 2))))
				phen_file.append("\nMedian: {:>18} ({})".format(str(round(compute_median(total), 2)), str(round(compute_median(normed), 2))))
				phen_file.append("\nStandard deviation: {:>6} ({})".format(str(round(compute_stan_deviation(total), 2)), str(round(compute_stan_deviation(normed), 2))))
				phen_file.append("\nStandard error: {:>10} ({})\n\n\n".format(str(round(compute_stan_error(total), 2)), str(round(compute_stan_error(normed), 2))))
				phen_file.append("Average Scores (Overall):\n-------------------------\n")
				phen_file.append("Average Semantic {}: {} ({})\n\n".format(s, round(float(average["Ann. Score"]), 3), round(float(norm(average["Ann. Score"], ss)), 3)))
				for met in your_wanted:
					phen_file.append("Tested Score ({}): {}\n\n".format(met, round(float(average[met.strip()]), 3)))
				# phen_file.extend(["{0:15} ---  {1}\n".format(metric, round(float(average[metric]), 3)) for metric in sorted(average.keys()) if metric in wanted])
				phen_file.extend([create_table_scores(sorted(average.keys()), [average[metric] for metric in sorted(average.keys())])])
				phen_file.append("\n\nCorrelation Matrix (Overall):\n-----------------------------\n")
				phen_file.append(tabulate(matrix, headers='keys', tablefmt='grid'))
				# phen_file.append(matrix.to_string())
				phen_file.append("\n\n===================================================================================================================================\n\n")
				# print("{} Data\n=========\n".format(ss.upper()))
				# print("Semantic {} Statistics:\n--------------------------------".format(s))
				# print("\nMean: {:>20}".format(str(round(compute_mean(total), 2))))
				# print("Median: {:>18}".format(str(round(compute_median(total), 2))))
				# print("Standard deviation: {:>6}".format(str(round(compute_stan_deviation(total), 2))))
				# print("Standard error: {:>10}\n\n".format(str(round(compute_stan_error(total), 2))))
				# print("Average Scores:\n---------------\n")
				# print("Average Semantic {}: {} ({})\n".format(s, round(float(average["Ann. Score"]), 3), round(float(norm(average["Ann. Score"], ss)), 3)))
				# for metric in sorted(average.keys()):
					# if metric in wanted:
						# print("{0:15} ---  {1}".format(metric, round(float(average[metric]), 3)))	
				# print(create_table_scores(sorted(average.keys()), [average[metric] for metric in sorted(average.keys())]))			
				# print("\n\nCorrelation Matrix:\n-------------------\n")
				# print(tabulate(matrix, headers='keys', tablefmt='grid'))
				# print(matrix.to_string())
				# print("\n")
				for phen in sorted(sub_phens.keys()):
					phen_ids = [idx for idx in sub_phens[phen]]
					all_used_ids[ss].extend(phen_ids)
					if len(sub_phens.keys()) > 1:
						corr_phen, av_phen = compute_av_scores(phen_ids, wanted, your_wanted, metric_dict)
						matrix_phen = frame(corr_phen)
						pp = ["-" for i in range(len(phen) + 6)]
						phen_file.append("{}\n   {}\n{}\n\n".format("".join(pp), phen, "".join(pp)))
						phen_file.append("Average Scores:\n---------------\n".format(phen))
						phen_file.append("Average Semantic {}: {} ({})\n\n".format(s, round(float(av_phen["Ann. Score"]), 3), round(float(norm(av_phen["Ann. Score"], ss)), 3)))
						for met in your_wanted:
							phen_file.append("Tested Score ({}): {}\n\n".format(met, round(float(av_phen[met]), 3)))
						# phen_file.extend(["{0:15} ---  {1}\n".format(metric, round(float(av_phen[metric]), 3)) for metric in sorted(av_phen.keys()) if metric in wanted])
						phen_file.extend([create_table_scores(sorted(av_phen.keys()), [av_phen[metric] for metric in sorted(av_phen.keys())])])
						phen_file.append("\n\nCorrelation Matrix:\n-------------------\n")
						phen_file.append(tabulate(matrix_phen, headers='keys', tablefmt='grid'))
						# phen_file.append(matrix_phen.to_string())
					phen_file.append("\n\n\nScores for Individual Test Cases:\n=================================\n\n")
					for idx in sub_phens[phen]:
						# print(idx)
						phen_file.append("{}\n---------\n\n".format(idx))
						try:
							phen_file.extend(print_testcase(vals[idx][1], vals[idx][2], vals[idx][0], {k:v for k,v in metric_dict[idx].items() if k in wanted or k in your_wanted}, vals[idx][3], rel))
						except IndexError:
							phen_file.extend(print_testcase(vals[idx][1], vals[idx][2], vals[idx][0], {k:v for k,v in metric_dict[idx].items() if k in wanted or k in your_wanted}, False, rel))							
					phen_file.append("\n\n------------------------------------------------------\n\n")
				write_file("../Results/{}_results.txt".format(phenomenon), phen_file)

	print(create_table_average(av_columns_sick, all_average_sick))
	print(create_table_average(av_columns, all_average))

	all_corr_sick, all_av_sick = compute_av_scores(all_used_ids["sick"], wanted, your_wanted, metric_dict)
	all_matrix_sick = frame(all_corr_sick)

	all_corr_sts, all_av_sts = compute_av_scores(all_used_ids["sts"], wanted, your_wanted, metric_dict)
	all_matrix_sts = frame(all_corr_sts)	

	print("-----------------\n     OVERALL\n-----------------\n\n")
	print("SICK Data Set\n=============\n")
	print("Correlation Matrix:\n-------------------")
	print(tabulate(all_matrix_sick, headers='keys', tablefmt='latex'))
	si = all_matrix_sick.unstack()
	for k,v in si["Ann. Score"].items():
		corr_hj_sick[k].append(v)
	print(create_cor_table(corr_hj_sick, av_columns_sick + ["Overall"]))
	for met in your_wanted:
		so = si[met].sort_values(kind="quicksort", ascending=False)
		print("\n\nOverall Correlation with Tested Score ({}):\n".format(met))
		print(so[1:].to_string())
	print("\n\nSTS Data Set\n============\n")
	print("Correlation Matrix:\n-------------------")
	print(tabulate(all_matrix_sts, headers='keys', tablefmt='latex'))
	st = all_matrix_sts.unstack()
	for k,v in st["Ann. Score"].items():
		corr_hj[k].append(v)
	print(create_cor_table(corr_hj, av_columns + ["Overall"]))
	for met in your_wanted:
		so = st[met].sort_values(kind="quicksort", ascending=False)
		print("\n\nOverall Correlation with Tested Score ({}):\n".format(met))
		print(so[1:].to_string())
		print("\n\n")