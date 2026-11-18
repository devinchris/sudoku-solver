# Konfiguration der Vorlage

Die gesamte Konfiguration der Arbeit erfolgt zentral in der Datei: `config/config.tex`.
Dort müssen die folgenden Variablen angepasst werden.

## Übersicht der Datei `config.tex`

```TeX
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Konfiguration %%

% --- Art der Arbeit ---
\def\myType{2}
%% 0=Projektarbeit
%% 1=Bachelorarbeit
%% 2=Sonstige Arbeiten (Seminararbeit, etc.)

% --- Titel & Autor ---
\def\myTopic{Titel der Arbeit}
\def\mySubTopic{Untertitel der Arbeit}
\def\myAutor{Max Mustermann}

% --- Akademische Infos ---
\def\myStudyProgram{Wirtschaftsinformatik} % Studiengang
\def\myNeedForFieldOfStudy{0}              % Studienrichtung benötigt? (0=Nein, 1=Ja)
\def\myFieldOfStudy{}                      % Name der Studienrichtung
\def\myCourse{WWI20A}                      % Kursbezeichnung
\def\myProf{Prof. Dr. Max Muster}          % Betreuer an der DHBW
\def\myEndDate{TT.MM.JJJJ}                 % Abgabedatum

% --- Betriebliche Infos ---
\def\myCompany{Musterfirma GmbH}           % Dualer Partner
\def\myCompanion{Betreuer im Betrieb}      % Begleitperson im Unternehmen

% --- Spezifisch für Projektarbeiten (myType=0) ---
\def\myProjNumber{1}                       % 1=Projektarbeit I, 2=Projektarbeit II

% --- Spezifisch für Bachelorarbeiten (myType=1) ---
\def\myTypeOfBachelor{Science}             % [Arts|Science|Engineering]

% --- Spezifisch für Sonstige Arbeiten (myType=2) ---
\def\myTypeOfWork{Seminararbeit}           % Text auf dem Titelblatt
\def\myModule{Modulname}                   % Modulbezeichnung
\def\myNames{0}                            % 0=Ein Autor, 1=Mehrere Autoren

% --- Spracheinstellungen ---
\newcommand{\myLanguage}{ngerman}          % [ngerman|english]

% --- Verzeichnisse (1=Anzeigen, 0=Ausblenden) ---
\def\myAbrevationDirectory{1}   % Abkürzungsverzeichnis
\def\myIllustrationDirectory{1} % Abbildungsverzeichnis
\def\myTableDirectory{1}        % Tabellenverzeichnis
\def\myListingDirectory{1}      % Listingverzeichnis
\def\myFormularDirectory{1}     % Formelverzeichnis
\def\mySymbolDirectory{1}       % Symbolverzeichnis
\def\myKiDirectory{1}           % KI-Verzeichnis

% --- Rechtliche Erklärungen (1=Anzeigen, 0=Ausblenden) ---
\def\myDecOfIndependence{1}     % Selbstständigkeitserklärung
\def\myBlockingNote{1}          % Sperrvermerk

% --- Ort und Datum für Unterschriften ---
\def\myDate{TT.MM.JJJJ}
\def\myPlace{Musterstadt}