# uvm_tb_gen
generate UVM testbench using python
python uvm_tb_gen.py -p project name -i list -o list 
    example 1: one input agent, one output agent,one ral agent:\n		python uvm_tb_gen.py -p uart -i uart -o apb -r apb\n" 
    example 2: two input agent:\n 		                              python uvm_tb_gen.py -p uart -i uart -i spi\n" 
