# SortNeurIPS
Sort [NeurIPS](https://nips.cc/) papers by the number of citations.

# Description
SortNeurIPS generates a sorted list of NeurIPS papers. It automatically searches NeurIPS paper on Google Scholar with Selenium webdriver and captures the number of citations. Codes are developed for internal usage at [SPA Laboratory](https://www.spa.hanyang.ac.kr/); use at your own risk.

# Usage

## Environment Setup
First, you need a Python 3 environment to run this program. Once you have the environment on your system, install the following dependencies: beautifulsoup4, pandas, selenium.
```
pip install -r requirements.txt
```

## Run
The program accepts the following arguments.

```
"--year" (required): A NeurIPS year to sort.

"--month" (optional): A NeurIPS month (Mostly "12" for recent events.). Used for calculating average citations per month.

"--csv (optional)": The location to save output *.csv file.
```

A basic usage is as follows. It will sort NeurIPS 2020 papers and output NeurIPS2020.csv.

```
python --year 2020
```

A Chrome (controlled by Selenium driver) window will open, and read the list of NeurIPS 2020 papers from the official proceedings page.
<p align="center"><img  src="./readme_assets/neurips_proceedings.png" width=70%></p>

Then, the program will automatically search each paper in the list and record its number of citations (See descriptions below if Google Scholar asks if you are not a robot).

<p align="center"><img  src="./readme_assets/progress.png" width="70%"></p>

Google Scholar sometimes asks you to solve captcha problems to prove that you are not a robot. Solve them until you pass the problems and see the search results. It is fine even if you get an empty results page.

<p align="center"><img  src="./readme_assets/good_result.png" width="70%"></p>

<p align="center"><img  src="./readme_assets/empty_result.png" width="70%"></p>

Once you get here, press ENTER on your terminal. The program will continue working. Note that you are likely to be asked to solve captcha multiple times while the program is working. Repeat the procedures so far whenever you are asked.

<p align="center"><img  src="./readme_assets/press_enter.png" width="70%"></p>

When finished, the program will output NeurIPS2020.csv at the current directory. The csv file will include paper ids, paper names, authors, citations (and yearly averages), sources. Papers are sorted in descending order.

<p align="center"><img  src="./readme_assets/result.png" width="70%"></p>

Optinally, you can add "--month" argument to calculate the number of citations per month. It is useful when the event happend within the past few months. NeurIPS is usally held on December.

```
python --year 2020 --month 12
```

You can also add "--csv" argument to set alternative location to save the output csv file.

```
python --year 2020 --month 12 --csv PATH_TO_THE_DIRECTORY
```

The program can restore from backup ("./temp/backup.pkl") saved while working. If the program is terminated for any reason just answer "Y" to the question upon the program's startup.

<p align="center"><img  src="./readme_assets/restore.png" width="70%"></p>