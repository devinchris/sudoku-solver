# Befehlsübersicht
Eine kurze übersicht über die wichtigesten Befehle die in der Vorlage enthalten sind


### Überschriften und Gliederung

```TeX
\section{erste Gliederungsebene}
\subsection{zweite Gliederungsebene}
\subsubsection{dritte Gliederungsebene}
\subsubsection{dritte Gliederungsebene}
```

### Text Style
```TeX
\glqq{}                                     % Anführungszeichen am Anfang
\grqq{}                                     % Anführungszeichen am Ende
\glqq Anführungszeichen\grqq{}              % Beispiel 
\textbf{Fettgedruckt}
\textit{Kursiv}		
\underline{Unterstrichen}
\\											% Manueller Zeilenumbruch
\myboxquote{Dieser Text steht in einer Box} % Für längere Zitate geeignet
```

### Referenzen und Verweise

```TeX
\label{referenzKey}     % Einen Referenzpunkt setzen
\ref{referenzKey}       % auf den referenzpunkt verweisen
\mypageref{referenzKey} % auf den referenzpunkt verweisen mit Seitenangabe
```
### Aufzählungen
Stichpunkte:
```TeX
\begin{itemize}								% Beginn einer Aufzählung
	\item erster Punkt						% Aufzählungspunkt
	\item Zweiter Punkt						% Aufzählungspunkt
\end{itemize}								% Ende der Aufzählung
```

Aufzählung:
```TeX
\begin{enumerate}								% Beginn einer Aufzählung
	\item erster Punkt						% Aufzählungspunkt
	\item Zweiter Punkt						% Aufzählungspunkt
\end{enumerate}								% Ende der Aufzählung
```

### Bilder
für genauere Erläuterung siehe hier:
```TeX
\begin{figure}[hbt]							% Beginn einer Grafik
	\centering 								% trim=left bottom right top
	\includegraphics[trim = 200mm 0mm 0mm 0mm, width=0.5\textwidth]{images/jubilaeum.jpg}
	\caption{Bild beschriftung} {\emph{\vgl[540]{BiBkey}}} % zweiter teil nicht im Verzeichnis
	\label{jubilaeum}
\end{figure}
```
### Tabelle
```TeX
\begin{table}[hbt]
\centering
\caption{Beschriftung {\emph{\vgl[540]{BiBkey}}}
\label{big5-korrelation}
	--> Tabelle einfügen. Als LaTeX tabelle oder Bild
\end{table}
```

### Literaturquellen

```TeX
% Indirekte Zitate (Sinngemäß) - nutzt Ihren \vgl Befehl
\vgl{BiBkey} 			% Erzeugt: (vgl. Autor, Jahr)
\vgl[2]{BiBkey} 		% Erzeugt: (vgl. Autor, Jahr, S. 2) - "S." wird automatisch ergänzt!
\vgl[13, 46]{BiBkey}	% Erzeugt: (vgl. Autor, Jahr, S. 13, 46)

% Direkte Zitate (Wörtlich) - KEIN vgl.
\parencite{BiBkey} 		% Erzeugt: (Autor, Jahr)
\parencite[2]{BiBkey} 	% Erzeugt: (Autor, Jahr, S. 2)

% Narratives Zitat (Im Satz)
\textcite{BiBkey} 		% Erzeugt: Autor (Jahr) - z.B.: "Wie Einstein (1905) sagte..."
```

### Abkürzungsverzeichnis
In dem Ordner chapter befindet sich die Datei abkuerzungsverzeichnis.tex. In dieser werden alle Abkürzungen definiert. Dabei sind diese wie das vorhandene Beispiel anzulegen. In die eckigen Klammern am Anfang der Datei muss die längste Abkürzung eingefügt werden, um eine optimale Formatierung zu erhalten.
Folgende Befehle können genutzt werden, um die Abkürzungen im Text zu verwenden:

Erste Verwendung: \ac{DHBW} – Zeigt „Duale Hochschule Baden-Württemberg (DHBW)“ an.
Nur Abkürzung: \acs{DHBW} – Zeigt nur die Abkürzung „DHBW“ an.
Nur ausgeschrieben: \acl{DHBW} – Zeigt nur den ausgeschriebenen Begriff an: „Duale Hochschule Baden-Württemberg“.
Pluralform: \acp{DHBW} – Zeigt „DHBWs“ an.