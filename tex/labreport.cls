\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{labreport}[2026/09/24 Neutral Japanese university lab report]

\LoadClass[a4paper,10pt,oneside]{ltjsarticle}

\RequirePackage[top=25mm,bottom=25mm,left=25mm,right=25mm]{geometry}
\RequirePackage{luatexja-fontspec}
\RequirePackage[haranoaji]{luatexja-preset}
\RequirePackage{setspace}
\RequirePackage{titlesec}
\RequirePackage{caption}
\RequirePackage{booktabs}
\RequirePackage{tabularx}
\RequirePackage{array}
\RequirePackage{graphicx}
\RequirePackage{flafter}
\RequirePackage{amsmath}
\RequirePackage{siunitx}
\RequirePackage{xurl}
\RequirePackage[hidelinks,unicode]{hyperref}
\RequirePackage{fancyhdr}
\RequirePackage{enumitem}
\RequirePackage{xcolor}
\RequirePackage{listings}
\RequirePackage{etoolbox}

\AtBeginDocument{\fontsize{10.5pt}{16.2pt}\selectfont}
\setlength{\parindent}{1\zw}
\setlength{\parskip}{0pt}
\setlength{\columnsep}{8mm}
\clubpenalty=10000
\widowpenalty=10000
\displaywidowpenalty=10000

\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\titleformat{\section}{\large\sffamily\bfseries}{\thesection}{0.8\zw}{}
\titleformat{\subsection}{\normalsize\sffamily\bfseries}{\thesubsection}{0.8\zw}{}
\titleformat{\subsubsection}{\normalsize\sffamily}{\thesubsubsection}{0.8\zw}{}
\titlespacing*{\section}{0pt}{2.0\baselineskip}{0.7\baselineskip}
\titlespacing*{\subsection}{0pt}{1.5\baselineskip}{0.5\baselineskip}
\titlespacing*{\subsubsection}{0pt}{1.2\baselineskip}{0.4\baselineskip}

\captionsetup{
  font={small,rm},
  labelfont=normalfont,
  labelsep=quad,
  justification=centering,
  singlelinecheck=true,
  skip=6pt
}
\captionsetup[table]{position=top,skip=6pt}
\captionsetup[figure]{position=bottom,skip=6pt}
\renewcommand{\figurename}{図}
\renewcommand{\tablename}{表}

\renewcommand{\topfraction}{0.88}
\renewcommand{\bottomfraction}{0.75}
\renewcommand{\textfraction}{0.10}
\renewcommand{\floatpagefraction}{0.75}
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{4}
\setlength{\textfloatsep}{14pt plus 4pt minus 3pt}
\setlength{\floatsep}{12pt plus 3pt minus 2pt}
\setlength{\intextsep}{14pt plus 4pt minus 3pt}

\sisetup{
  detect-all,
  per-mode=symbol,
  range-phrase=--,
  range-units=single
}
\urlstyle{same}
\hypersetup{pdfborder={0 0 0}}

\lstset{
  basicstyle=\small\ttfamily,
  numbers=left,
  numberstyle=\scriptsize,
  numbersep=0.8em,
  frame=single,
  framerule=0.3pt,
  rulecolor=\color{black!35},
  backgroundcolor=\color{black!2},
  breaklines=true,
  breakatwhitespace=false,
  showstringspaces=false,
  columns=fullflexible,
  keepspaces=true,
  captionpos=t,
  aboveskip=1.0\baselineskip,
  belowskip=0.8\baselineskip
}
\renewcommand{\lstlistingname}{リスト}

\newcommand{\ReportCourse}{}
\newcommand{\ReportTitle}{}
\newcommand{\ReportSubtitle}{}
\newcommand{\ReportFields}{}
\newcommand{\reportcourse}[1]{\renewcommand{\ReportCourse}{#1}}
\newcommand{\reporttitle}[1]{\renewcommand{\ReportTitle}{#1}}
\newcommand{\reportsubtitle}[1]{\renewcommand{\ReportSubtitle}{#1}}
\newcommand{\reportfield}[2]{%
  \gappto\ReportFields{#1 & #2 \\[0.65em]}%
}

\newcommand{\makelabcover}{%
  \pagenumbering{gobble}
  \begin{titlepage}
    \thispagestyle{empty}
    \centering
    \vspace*{18mm}
    {\large\sffamily \ReportCourse\par}
    \vspace{24mm}
    {\fontsize{22pt}{31pt}\selectfont\sffamily\bfseries \ReportTitle\par}
    \ifstrempty{\ReportSubtitle}{}{\vspace{5mm}{\large\sffamily \ReportSubtitle\par}}
    \vfill
    \begin{tabular}{@{}>{\sffamily\bfseries\raggedleft\arraybackslash}p{7em}@{\hspace{1.5em}}>{\raggedright\arraybackslash}p{18em}@{}}
      \ReportFields
    \end{tabular}
    \vspace*{16mm}
  \end{titlepage}
  \clearpage
  \pagenumbering{arabic}
}

\newcommand{\sourcecite}[1]{\textsuperscript{[#1]}}

\renewenvironment{thebibliography}[1]
  {\section*{参考文献}%
   \addcontentsline{toc}{section}{参考文献}%
   \list{[\arabic{enumiv}]}%
     {\settowidth\labelwidth{[#1]}%
      \leftmargin\labelwidth
      \advance\leftmargin\labelsep
      \usecounter{enumiv}%
      \setlength{\itemsep}{0.35\baselineskip}%
      \setlength{\parsep}{0pt}}%
   \sloppy}
  {\endlist}
