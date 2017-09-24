dot -Tpdf -o diagram.pdf <(
    echo 'digraph "G" {'
        cat ../data/elmap.txt | perl -pe 's/(.*)=(.*)\+(.*)/$2->$1; $3->$1;/'
    echo '}'
)

okular diagram.pdf
