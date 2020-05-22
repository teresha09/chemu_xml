python XML2JSON -data applications -out train -files 50  
python json2conll -vocab BIOBERT_DIR/vocab.txt -entity reaction_product,solvent,time,temperature -json train.json -out train