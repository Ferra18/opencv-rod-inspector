# VISUAL INSPECTION OF CONNECTING RODS

## Primo task
---

### Segmentazione

Per prima cosa si è proceduto alla segmentazione dell'immagine. Nonostante la consegna specifichi che le immagini sono state acquisite con tecniche di *backlighting*, quindi il contrasto degli oggetti con lo sfondo è molto elevato. La consegna chiede comunque che il sistema possa funzionare anche con fonti di luce differente, quindi è stato utilizzato l'algoritmo di Otsu già implementato nella libreria di OpenCV, che permette di identificare un valore di soglia per la binarizzazione in maniera automatica (garantendo quindi un funzionamento migliore nel caso cambiassero le fonti di illuminazione).

### Identificazione degli oggetti

Per l'identificazione si è utilizzata la funzione di libreria *findContours*. Questa restituisce la lista dei contorni degli oggetti (sottoforma di punti, pixel) e la gerarchia di questi contorni.

Con una semplice funzione si può interpretare la gerarchia dei contorni, individuando se all'interno di ognuno di essi ne sono presenti altri. I contorni di primo livello possono quindi essere identificati come *rod* (a meno di condizioni che dopo vedremo), mentre quelli a profondità maggiore sono identificati come *hole* e sono associati alla rod specificata nella gerarchia (sia rod che hole sono implementati come classi).

Associando gli hole alla rispettiva rod si identifica la tipologia di rod, che viene salvata all'interno dell'oggetto.

Ad ogni creazione di un rod o di un hole sono inoltre associati i pixel che ne identificano il contorno che saranno utilizzati per le successive operazioni.

### Dimensioni dell'oggetto

Avendo a disposizione i pixel che ne formano il contorno, è possibile utilizzare i metodi *contourArea* e *minAreaRect* per calcolare rispettivamente l'area interna al contorno e il rettangolo con l'area minima che lo contiene. Da questo rettangolo (*bounding_rect*) è possibile ricavare le dimensioni quali lunghezza e larghezza.

Per quanto riguarda l'area della rod, è opportuno ricordarsi di sottrarre le aree degli hole associati ad esso dopo aver utilizzato la funzione *contourArea*.

I diametri degli hole sono calcolati partendo dall'area data da *minAreaRect* secondo la formula del diametro `d=sqrt(4*area/π)`.

### Posizione e orientazione

Per identificare la posizione dell'oggetto si è utilizzato il suo baricentro, calcolato utilizzando il momento dell'immagine.

Per quanto riguarda l'orientazione si è invece ricorso alla *PCA*, *Principal Component Analysis*, che permette di identificare l'orientazione dei due assi dell'oggetto.

### Larghezza al baricentro

La larghezza dell'oggetto al baricentro non è altro che la distanza tra i due punti del contorno che appartengono alla retta passante per il baricentro e parallela all'asse minore. 

Tramite i precedenti calcoli conosciamo sia le coordinate del baricentro che l'angolo che l'asse minore forma con l'asse delle ascisse. Si possono quindi trovare facilmente il coefficiente angolare *m* e l'intercetta *q* che caratterizzano la retta `y=mx+q` passante per il baricentro e parallela all'asse minore. 

Mettendo a sistema i pixel del contorno con l'equazione della retta si trovano i due punti con i quali calcolare la larghezza. Occorre però prestare attenzione alle approssimazioni, in quanto ogni pixel è rappresentato da *x* e *y* intere mentre molto probabilmente le coordinate ottenibili dalla retta sono reali.

Per ogni punto del contorno viene quindi calcolato il valore di *y* utilizzando l'equazione della retta trovata e la coordinata *x* del pixel. Per ogni punto viene quindi calcolata la differenza `d=|y-y_P|` tra l'*y* calcolata e l'*y* reale del pixel e vengono estratti i due pixel che hanno questa differnza minima che rappresenrano gli estremi della larghezza al baricentro.

## Secondo task
---

### Polvere di ferro

La polvere di ferro presente in alcune immagini piò essere rimossa semplicemente attraverso l'applicazione di uno o più filtri mediani. 

Visto che in alcune immagini il rumore è piuttosto forte, sono stati applicati tre filtri *medianBlur* con kernel 3x3 in cascata.

### Rimozione di altri oggetti

Per rimuovere e quindi non considerare gli oggetti che non sono rod (nel caso di queste immagini viti e bulloni) viene leggermente modificato il metodo di interpretazione della gerarchia.

Gli oggetti che non contengono hole, e quindi che nella gerarchia non hanno figli, non vengono più classificati come rod in quanto rappresentano viti o altri oggetti "senza buchi".

Per non considerare i bulloni, i quali sono caratterizzati da un foro e da una forma circolare del contorno, viene calcolata l'eccentricità di ciascun contorno dopo aver estratto l'ellisse e i suoi assi con il metodo *fitEllipse*. Empiricamente si è trovato che i bulloni hanno in genere eccentricità minori di 0.7 e si è quindi utilizzato questo valore per discriminarli dalle rod.

### Punti di contatto

Le rod che hanno punti di contatto vengono riconosciute come un unico contorno e quindi sono caratterizzate da un'area molto maggiore rispetto alle rod "normali". 

È stato quindi ricavato empiricamente che questi contorni contenenti due o più rod a contatto hanno un'area superiore ai settemila pixel. 

Per ciascuno di questi contorni è quindi stato applicato il metodo *approxPolyDP* per semplificare e diminuire il numero di vertici del contorno e il metodo *convexHull* per ottenere l'inviluppo convesso più piccolo contenente il contorno. Sono quindi stati identificati i *defect points* tramite il metodo *convexityDefects*: non sono altro che i punti nei quali la distanza tra il punto del contorno e il corrispettivo punto dell'inviluppo convesso è maggiore, e rappresentano geometricamente i punti di contatto. Da quesi punti si può quindi tracciare una linea che andà ad unirsi al background e dividerà le varie rod, che a questo punto possono essere analizzate correttamente con la precedente implementazione.

## Conclusioni

In conclusione, le tecniche utilizzate hanno permesso di raggiungere un risultato abbastanza soddisfacente.

I punti più ardui da affrontare sono stati sicuramente il calcolo della larghezza al baricentro e la divisione di rob con punti di contatto. Per via delle immagini di bassa qualità è più difficile identificare correttamente i pixel appartenenti alla retta parallela all'asse minore a causa delle approssimazioni che devono essere effettuate. Discorso simile per quanto riguarda la divisione delle rod, a cui si aggiunge il problema della linea di divisione: in alcuni casi può andare infatti ad intaccare l'hole di una delle due rod, facendo fallire così la classificazione per via di una rod "aperta".