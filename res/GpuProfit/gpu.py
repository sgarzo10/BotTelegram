from urllib.request import Request, urlopen
from tabulate import tabulate

f = open("gpus.txt", "r")
ctx = f.read()
gpu_list = ctx.split("\n")
revenue_list = []
gpu_scan = 0
max_row = 0
for gpu in gpu_list:
    req = Request('https://2cryptocalc.com/gpu/now/' + gpu + '/1')
    req.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36')
    content = str(urlopen(req).read())
    print(gpu)
    j = 0
    content_split = content.split("<td class=\"col-green column_desktop text-right\"")[1:]
    for s in content_split:
        s = s.split("</td>")[0]
        dollari = s.split("<span class=\"text-val\">")[1].split("</span>")[0] + "$"
        crypto = s.split("<span class=\"text-gray text-gray_size-small\">")[1].split("</span>")[0]
        if len(revenue_list) <= j:
            new_row = []
            for i in range(gpu_scan):
                new_row.append("")
            revenue_list.append(new_row)
        revenue_list[j].append(dollari + " " + crypto)
        j = j + 1
    if j >= max_row:
        max_row = j
    else:
        for k in range(max_row - j):
            revenue_list[k + j].append("")
    gpu_scan = gpu_scan + 1
f = open("output.txt", "w")
f.write(tabulate(revenue_list, headers=gpu_list))
f.close()
