#!usr/bin/python
##
##-------------------------------------------------
##generate uvm tb , basically including 5 level structure. top/test/env/agent/seq/seqer/driver/monitor/interface, scb/refm/cov/assertion/seqlib
##project
##      +rtl
##      +doc
##      +dv
##          +tb
##          +env
##          +agent
##          +tests
##            +seqlib
##          +sim    
##            +scripts
##this script is based on an open uvm_tb_gen.pl please contact  getwkg@163.com.
# ***********************************************************************
# *****   *********       Copyright (c) 2018 
# ***********************************************************************
# PROJECT        : 
# FILENAME       : uvm_tb_gen.py
# Author         : [dpc525@163.com]
# LAST MODIFIED  : 2018-03-24 16:06
# ***********************************************************************
# DESCRIPTION    :
# ***********************************************************************
# $Revision: $
# $Id: $
# ***********************************************************************
#--------------------------------------------------
import re
import sys
import os
import getopt

def usage():
    print  "	********USAGE: python uvm_tb_gen.py -help/h (print this message)********\n" 
    print  "	this scritps support several input agent, output agent, agent with ral" 
    print  "	for the ral agent, support adapter for i2c/spi/apb/ahb,not support yet." 
    print  "	Any suggestion, please contact  dpc525@163.com" 
    print  "	python uvm_tb_gen.py -p project name -i list (input agent name)/active -o list (output agent name)/passive -r register agent with ral\n" 
    print  "	example 1: one input agent, one output agent,one ral agent:\n		python uvm_tb_gen.py -p uart -i uart -o localbus -r apb\n" 
    print  "	example 2: two input agent:\n 		                                python uvm_tb_gen.py -p uart -i uart localbus\n" 
    print  "	example 3: two input agent, one output agent,two ral agent:\n 		python uvm_tb_gen.py -p uart -i uart localbus -o outp -r apb ahb\n" 
    print  "	********************************************************************\n" 

def tb_gen(argv):
    global project    #= "--undef--"
    global tbname     #= "--undef--"
    global envname     #= "--undef--"
    global agent_name #= "--undef--"
    global agent_if   #= "--undef--"
    global agent_item #= "--undef--"
    global agent_list

    mode = "irun"
    i_agt=[]
    o_agt=[]

    try:
        opts, args = getopt.getopt(argv, "p:i:i:o:runvcs", ["project", "agent"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            usage()
            sys.exit()

        elif opt in("-p", "project"):
            project = arg
        elif opt in("-i"):
            agent_name = arg
            i_agt.append(arg)
        elif opt in("-o"):
            o_agt.append(arg)
        elif opt in("-irun"):
            mode = "irun" 
        elif opt in("-vcs"):
            mode = "vcs" 

    tbname = project 
    envname = project+"_env"
    agent_list = i_agt + o_agt

    print "The project name is", project
    print "The agent name is"  , agent_name
    print "The simulator is "  , mode
    print "\nParsing  Input Agent ...\n\n"
    print "Writing code to files"
    if os.path.exists(project+"/doc/") != True:
        os.makedirs(project+"/doc/")

    if os.path.exists(project+"/rtl/") != True:
        os.makedirs(project+"/rtl/")

    if os.path.exists(project+"/dv/env/")!= True:
        os.makedirs(project+"/dv/env/")

    if os.path.exists(project+"/dv/tb/")!= True:
        os.makedirs(project+"/dv/tb/")

    if os.path.exists(project+"/dv/sim/")!= True:
        os.makedirs(project+"/dv/sim/")
    #os.makedirs(project+"/dv/tests/")
    if os.path.exists(project+"/dv/tests/test_seq") != True :
        os.makedirs(project+"/dv/tests/test_seq")

    template_type = "act"
    for agt in i_agt:
        if os.path.exists(project+"/dv/agent/"+agt)!= True:
            os.makedirs(project+"/dv/agent/"+agt)
        #create the agent files
        agent_name = agt
        agent_if = agent_name+"_if"
        agent_item = agent_name+"_seq_item"
        gen_if() 
        gen_seq_item() 
        gen_config(template_type) 
        if(template_type == "act"): 
            gen_driver() 
            gen_seq() 
            gen_sequencer() 

        gen_monitor() 
        gen_agent(template_type) 
        gen_agent_pkg(template_type) 
    template_type = "pas"
    for agt in o_agt:
        if os.path.exists(project+"/dv/agent/"+agt)!= True:
            os.makedirs(project+"/dv/agent/"+agt)
        #create the agent files
        agent_name = agt
        agent_if = agent_name+"_if"
        agent_item = agent_name+"_seq_item"
        gen_if() 
        gen_seq_item() 
        gen_config(template_type) 
        #if(template_type == "act"): 
        #    gen_driver() 
        #    gen_seq() 
        #    gen_sequencer() 
        gen_monitor() 
        gen_agent(template_type) 
        gen_agent_pkg(template_type) 
    # gen_cov() 
    gen_refm()
    gen_scb()

    # gen_tb();
    # gen_test();
    gen_top_test();
    gen_top()
    gen_top_config()
    gen_top_env()
    gen_top_pkg()

    #gen_questa_script();
    if mode == "irun":
        gen_irun_script()
    else:
        gen_vcs_script()


def write_file_header(file_f):
    #f = open(file_f, "w")
    #old = f.read()
    #f.seek(0)
    print >>file_f, "//============================================================================="
    print >>file_f, "// copyright";
    print >>file_f, "//============================================================================="
    print >>file_f, "// Project  : "+project+""
    print >>file_f, "// File Name: $fname"
    print >>file_f, "// Author   : Name   : $name"
    print >>file_f, "//            Email  : $email"
    print >>file_f, "//            Dept   : $dept"
    print >>file_f, "// Version  : $version"
    print >>file_f, "//============================================================================="
    print >>file_f, "// Description:"
    print >>file_f, "//=============================================================================\n"
#end def write_file_header


def gen_if(): 
    global project

    dir_path = project+"/dv/agent/"+agent_name+"/"
    try:
        if_f = open( dir_path+agent_name+"_if.sv","w" )
    except IOError:
        print "Exiting due to Error: can't open interface: "+agent_name 

    write_file_header(if_f)
    print >> if_f,   "`ifndef "+agent_name.upper()+"_IF_SV" 
    print >> if_f,   "`define "+agent_name.upper()+"_IF_SV\n" 

    print >> if_f,   "interface "+agent_if+"(); \n" 

    print >> if_f,   "  // You could add properties and assertions, for example" 
    print >> if_f,   "  // property name " 
    print >> if_f,   "  // ..." 
    print >> if_f,   "  // endproperty : name" 
    print >> if_f,   "  // label: assert property(name) \n" 

    print >> if_f,   "endinterface : "+agent_if+"\n" 
    print >> if_f,   "`endif // "+agent_name.upper()+"_IF_SV" 
    if_f.close( ) 
#end gen_if


def gen_seq_item():
    global project

    dir_path = project+"/dv/agent/"+agent_name+"/"
    try:
        tr_f = open( dir_path+agent_item+".sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open data_item: "+agent_item

    write_file_header(tr_f)
    print >>tr_f, "`ifndef " +agent_item.upper()+"_SV";
    print >>tr_f, "`define " +agent_item.upper()+"_SV\n";

    print >>tr_f, "class "+agent_item+" extends uvm_sequence_item; "
    print >>tr_f, "  `uvm_object_utils("+agent_item+")\n";
    print >>tr_f, "  extern function new(string name = \""+agent_item+"\");\n";

    print >>tr_f, "endclass : "+agent_item+" \n";

    print >>tr_f, "function "+agent_item+"::new(string name = \""+agent_item+"\");";
    print >>tr_f, "  super.new(name);";
    print >>tr_f, "endfunction : new\n";

    print >>tr_f, "`endif // "+agent_item.upper()+"_SV\n"
    tr_f.close()
#end gen_data_item


def gen_config(template_type):
    global project

    dir_path = project+"/dv/agent/"+agent_name+"/"

    print "type = $template_type,   agent name = "+agent_name+"\n";
    try:
        cfg_f = open(dir_path+agent_name+"_agent_config.sv", "w")
    except IOError:
        print "Exiting due to Error: can't open config: "+agent_name
    write_file_header(cfg_f)

    print >> cfg_f, "`ifndef " +agent_name.upper()+"_AGENT_CONFIG_SV";
    print >> cfg_f, "`define " +agent_name.upper()+"_AGENT_CONFIG_SV\n";

    print >> cfg_f, "class "+agent_name+"_agent_config extends uvm_object;";
      
    print >> cfg_f, "  `uvm_object_utils("+agent_name+"_agent_config)\n";
    if(template_type == "pas"):
        print >> cfg_f, "  rand uvm_active_passive_enum is_active = UVM_PASSIVE;\n";
    else:
        print >> cfg_f, "  rand uvm_active_passive_enum is_active = UVM_ACTIVE;\n";

    print >> cfg_f, "  rand bit coverage_enable = 0;";
    print >> cfg_f, "  rand bit checks_enable = 0;";

    print >> cfg_f, "  extern function new(string name = \""+agent_name+"\_agent_config\");\n"

    print >> cfg_f, "endclass : "+agent_name+"_agent_config \n"
    print >> cfg_f, "function "+agent_name+"_agent_config::new(string name = \""+agent_name+"\_agent_config\");"
    print >> cfg_f, "  super.new(name);";
    print >> cfg_f, "endfunction : new\n";

    print >> cfg_f, "`endif // " +agent_name.upper()+"_AGENT_CONFIG_SV\n";
    cfg_f.close()
##end gen_config


def gen_driver():
    global project

    dir_path = project+"/dv/agent/"+agent_name+"/"
    try:
        drv_f = open(dir_path+agent_name+"_driver.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open driver: "+agent_name

    write_file_header(drv_f)

    print >>drv_f, "`ifndef "+agent_name.upper()+"_DRIVER_SV"
    print >>drv_f, "`define "+agent_name.upper()+"_DRIVER_SV\n"

    print >>drv_f, "class "+agent_name+"_driver extends uvm_driver #("+agent_item+");"
    print >>drv_f, "  `uvm_component_utils("+agent_name+"_driver)\n"

    print >>drv_f, "  virtual interface  "+agent_if+" vif;\n"

    print >>drv_f, "  extern function new(string name, uvm_component parent);"
    print >>drv_f, "  extern virtual function void build_phase (uvm_phase phase);"
    print >>drv_f, "  extern virtual function void connect_phase(uvm_phase phase);"      
    print >>drv_f, "  extern task main_phase(uvm_phase phase);"
    print >>drv_f, "  extern task do_drive("+agent_item+" req);\n"
    print >>drv_f, "endclass : "+agent_name+"_driver\n"

    print >>drv_f, "function "+agent_name+"_driver::new(string name, uvm_component parent);"
    print >>drv_f, "  super.new(name, parent);";
    print >>drv_f, "endfunction : new\n"

    print >>drv_f, "function void "+agent_name+"_driver::build_phase(uvm_phase phase);"
    print >>drv_f, "  super.build_phase(phase);"
    print >>drv_f, "endfunction : build_phase\n"

    print >>drv_f, "function void "+agent_name+"_driver::connect_phase(uvm_phase phase);"
    print >>drv_f, "  super.connect_phase(phase);\n"
    print >>drv_f, "  if (!uvm_config_db #(virtual "+agent_name+'_if)::get(this, "*", "' +agent_name+"_vif\", vif))"
    print >>drv_f, "    `uvm_error(\"NOVIF\", {\"virtual interface must be set for: \",get_full_name(),\".vif\"})\n"
    print >>drv_f, "endfunction : connect_phase\n"

    print >>drv_f, "task "+agent_name+"_driver::main_phase(uvm_phase phase);"
    #print >>drv_f, "  super.run_phase(phase);\n";
    print >>drv_f, "  `uvm_info(get_type_name(), \"main_phase\", UVM_HIGH)\n"
    print >>drv_f, "  forever";
    print >>drv_f, "  begin";
    print >>drv_f, "    seq_item_port.get_next_item(req);\n";
    print >>drv_f, "      `uvm_info(get_type_name(), {\"req item\\n\",req.sprint}, UVM_HIGH)\n";
    print >>drv_f, "    do_drive(req);\n";
    print >>drv_f, "    //$cast(rsp, req.clone());";
    print >>drv_f, "    seq_item_port.item_done();";
    print >>drv_f, "    # 10ns;\n";
    print >>drv_f, "  end\n";
    print >>drv_f, "endtask : main_phase\n";

    print >>drv_f, "task "+agent_name+"_driver::do_drive("+agent_item+" req);\n\n";
    print >>drv_f, "endtask : do_drive\n";

    print >>drv_f, "`endif // "+agent_name.upper()+"_DRIVER_SV\n\n";
    drv_f.close();
#end def gen_driver


def gen_monitor(): 
    global project

    dir_path = project+"/dv/agent/"+agent_name+"/"
    try:
        mon_f = open( dir_path+agent_name+"_monitor.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open monitor: "+agent_name
#
#    write_file_header ""+agent_name+"_monitor.sv", "Monitor for "+agent_name+"";
    print >> mon_f, "`ifndef "+agent_name.upper()+"_MONITOR_SV"
    print >> mon_f, "`define "+agent_name.upper()+"_MONITOR_SV\n"

    print >> mon_f, "class "+agent_name+"_monitor extends uvm_monitor;"
    print >> mon_f, "  `uvm_component_utils("+agent_name+"_monitor)\n"
    print >> mon_f, "  virtual interface  "+agent_if+" vif;\n"
    print >> mon_f, "  uvm_analysis_port #("+agent_item+") analysis_port;\n";

    print >> mon_f, "  "+agent_item+" m_trans;\n";

    print >> mon_f, "  extern function new(string name, uvm_component parent);"
    print >> mon_f, "  extern virtual function void build_phase (uvm_phase phase);"
    print >> mon_f, "  extern virtual function void connect_phase(uvm_phase phase);"    
    print >> mon_f, "  extern task main_phase(uvm_phase phase);"
    print >> mon_f, "  extern task do_mon();\n"

    print >> mon_f, "endclass : "+agent_name+"_monitor \n"
    print >> mon_f, "function "+agent_name+"_monitor::new(string name, uvm_component parent);\n"
    print >> mon_f, "  super.new(name, parent);"
    print >> mon_f, "  analysis_port = new(\"analysis_port\", this);\n"
    print >> mon_f, "endfunction : new\n"

    print >> mon_f, "function void "+agent_name+"_monitor::build_phase(uvm_phase phase);\n"
    print >> mon_f, "  super.build_phase(phase);\n"
    print >> mon_f, "endfunction : build_phase\n"

    print >> mon_f, "function void "+agent_name+"_monitor::connect_phase(uvm_phase phase);"
    print >> mon_f, "  super.connect_phase(phase);\n"
    print >> mon_f, "  if (!uvm_config_db #(virtual "+agent_name+'_if)::get(this, "*", "' +agent_name+"_vif\", vif))"
    #print >> mon_f, "  if (!uvm_config_db #(virtual "+agent_name+')::get(this, "",' +agent_name+"_vif, vif))"
    print >> mon_f, "    `uvm_error(\"NOVIF\",{\"virtual interface must be set for: \",get_full_name(),\".vif\"})\n"
    print >> mon_f, "endfunction : connect_phase\n"

    print >> mon_f, "task "+agent_name+"_monitor::main_phase(uvm_phase phase);"
    print >> mon_f, "  `uvm_info(get_type_name(), \"main_phase\", UVM_HIGH)\n"
    print >> mon_f, "  m_trans = "+agent_item+"::type_id::create(\"m_trans\");"
    print >> mon_f, "  do_mon();\n"
    print >> mon_f, "endtask : main_phase\n"

    print >> mon_f, "task "+agent_name+"_monitor::do_mon();\n";
    print >> mon_f, "endtask : do_mon\n";

    print >> mon_f, "`endif // "+agent_name.upper()+"_MONITOR_SV\n\n";
    mon_f.close();
 #end def gen_monitor 


def gen_sequencer(): 
    global project

    dir_path = project+"/dv/agent/"+agent_name+"/"
    try:
        sqr_f = open(dir_path+agent_name+"_sequencer.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open sequencer: "+agent_name

    write_file_header(sqr_f)

    print >> sqr_f, "`ifndef "+agent_name.upper()+"_SEQUENCER_SV";
    print >> sqr_f, "`define "+agent_name.upper()+"_SEQUENCER_SV\n";

    print >> sqr_f, "class "+agent_name+"_sequencer extends uvm_sequencer #("+agent_item+");";
    print >> sqr_f, "  `uvm_component_utils("+agent_name+"_sequencer)\n";

    print >> sqr_f, "  extern function new(string name, uvm_component parent);\n";

    print >> sqr_f, "endclass : "+agent_name+"_sequencer \n";

    print >> sqr_f, "function "+agent_name+"_sequencer::new(string name, uvm_component parent);\n";
    print >> sqr_f, "  super.new(name, parent);\n";
    print >> sqr_f, "endfunction : new\n";

    print >> sqr_f, "`endif // "+agent_name.upper()+"_SEQUENCER_SV\n\n";
    sqr_f.close();
#end def gen_sequencer


def gen_agent(template_type):
    global project

    dir_path = project+"/dv/agent/"+agent_name+"/"

    try:
        agt_f = open(dir_path+agent_name+"_agent.sv", "w")
    except IOError:
        print "Exiting due to Error: can't open sequencer: "+agent_name
    write_file_header(agt_f)

    print >> agt_f,  "`ifndef " +agent_name.upper()+ "_AGENT_SV" 
    print >> agt_f,  "`define " +agent_name.upper()+ "_AGENT_SV\n" 

    print >> agt_f,  "class "+agent_name+"_agent extends uvm_agent;" 
    print >> agt_f,  "  "+agent_name+"_agent_config       m_cfg;" 
    if(template_type == "act"):
        print >> agt_f,  "  "+agent_name+"_sequencer          m_sequencer;" 
        print >> agt_f,  "  "+agent_name+"_driver             m_driver;" 

    print >> agt_f,  "  "+agent_name+"_monitor            m_monitor;\n" 

    print >> agt_f,  "  uvm_analysis_port #("+agent_item+") analysis_port;\n" 
    print >> agt_f,  "  `uvm_component_utils_begin("+agent_name+"_agent)" 
    print >> agt_f,  "     `uvm_field_enum(uvm_active_passive_enum, is_active, UVM_DEFAULT)" 
    print >> agt_f,  "     `uvm_field_object(m_cfg, UVM_DEFAULT | UVM_REFERENCE)" 
    print >> agt_f,  "  `uvm_component_utils_end\n" 

    print >> agt_f,  "  extern function new(string name, uvm_component parent); \n" 
    print >> agt_f,  "  extern function void build_phase(uvm_phase phase);" 
    print >> agt_f,  "  extern function void connect_phase(uvm_phase phase);\n" 

    print >> agt_f,  "endclass : "+agent_name+"_agent" 
    print >> agt_f,  "\n" 

    print >> agt_f,  "function  "+agent_name+"_agent::new(string name, uvm_component parent);" 
    print >> agt_f,  "  super.new(name, parent);" 
    print >> agt_f,  "  analysis_port = new(\"analysis_port\", this);" 
    print >> agt_f,  "endfunction : new" 
    print >> agt_f,  "\n" 

    print >> agt_f,  "function void "+agent_name+"_agent::build_phase(uvm_phase phase);" 
    print >> agt_f,  "  super.build_phase(phase);\n" 
    print >> agt_f,  "  if(m_cfg == null) begin" 
    print >> agt_f,  "    if (!uvm_config_db#("+agent_name+"_agent_config)::get(this, \"\", \"m_cfg\", m_cfg))\n    begin" 
    print >> agt_f,  "      `uvm_warning(\"NOCONFIG\", \"Config not set for Rx agent, using default is_active field\")" 
    print >> agt_f,  "      m_cfg = "+agent_name+"_agent_config  ::type_id::create(\"m_cfg\", this);" 
    print >> agt_f,  "    end" 
    print >> agt_f,  "  end" 
    print >> agt_f,  "  is_active = m_cfg.is_active;\n" 

    print >> agt_f,  "  m_monitor     = "+agent_name+"_monitor    ::type_id::create(\"m_monitor\", this);" 
    if( template_type == "act"):
        print >> agt_f,  "  if (is_active == UVM_ACTIVE)" 
        print >> agt_f,  "  begin" 
        print >> agt_f,  "    m_driver    = "+agent_name+"_driver     ::type_id::create(\"m_driver\", this);" 
        print >> agt_f,  "    m_sequencer = "+agent_name+"_sequencer  ::type_id::create(\"m_sequencer\", this);" 
        print >> agt_f,  "  end" 
    print >> agt_f,  "endfunction : build_phase" 
    print >> agt_f,  "\n" 
    
    print >> agt_f,  "function void "+agent_name+"_agent::connect_phase(uvm_phase phase);" 
    print >> agt_f,  "  super.connect_phase(phase);\n" 
    print >> agt_f,  "  m_monitor.analysis_port.connect(analysis_port);" 
    if( template_type == "act"):
        print >> agt_f,  "  if (is_active == UVM_ACTIVE)" 
        print >> agt_f,  "  begin" 
        print >> agt_f,  "    m_driver.seq_item_port.connect(m_sequencer.seq_item_export);" 
        print >> agt_f,  "  end" 

    print >> agt_f,  "endfunction : connect_phase\n" 
    print >> agt_f,  "`endif // "+agent_name.upper()+"_AGENT_SV\n\n" 
    agt_f.close()


def gen_seq(): 
    global project

    dir_path = project+"/dv/tests/test_seq/"
    try:
        seq_f = open( dir_path+agent_name+"_seq.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open seq: "+agent_name
    write_file_header(seq_f)

    print >>seq_f, "`ifndef "+agent_name.upper()+"_SEQ_SV"
    print >>seq_f, "`define "+agent_name.upper()+"_SEQ_SV\n"

    print >>seq_f, "class "+agent_name+"_base_seq extends uvm_sequence #("+agent_item+");"
    print >>seq_f, "  `uvm_object_utils("+agent_name+"_base_seq)\n"

    print >>seq_f, "  function new(string name = \""+agent_name+"_base_seq\");"
    print >>seq_f, "    super.new(name);"
    print >>seq_f, "  endfunction\n"
    print >>seq_f, "  virtual task pre_body();";
    print >>seq_f, "    if (starting_phase != null)\n";
    print >>seq_f, "    starting_phase.raise_objection(this, {\"Running sequence '\","
    print >>seq_f, "                                          get_full_name(), \"'\"});\n";
    print >>seq_f, "  endtask\n";
    print >>seq_f, "  virtual task post_body();";
    print >>seq_f, "    if (starting_phase != null)";
    print >>seq_f, "    starting_phase.drop_objection(this, {\"Completed sequence '\",";
    print >>seq_f, "                                         get_full_name(), \"'\"});\n";
    print >>seq_f, "  endtask\n";
    print >>seq_f, "endclass : "+agent_name+"_base_seq\n";
    print >>seq_f, "//-------------------------------------------------------------------------\n"; 
    
    print >>seq_f, "class "+agent_name+"_seq extends "+agent_name+"_base_seq;"; 
    print >>seq_f, "  `uvm_object_utils("+agent_name+"_seq)\n";

    print >>seq_f, "  extern function new(string name = \""+agent_name+"\_seq\");\n";
    print >>seq_f, "  extern task body();\n";
    print >>seq_f, "endclass : "+agent_name+"_seq\n";

    print >>seq_f, "function "+agent_name+"_seq::new(string name = \""+agent_name+"_seq\");";
    print >>seq_f, "  super.new(name);";
    print >>seq_f, "endfunction : new\n";

    print >>seq_f, "task "+agent_name+"_seq::body();\n";
    print >>seq_f, "  `uvm_info(get_type_name(), \"Default sequence starting\", UVM_HIGH)\n\n";
    print >>seq_f, "  req = "+agent_item+"::type_id::create(\"req\");\n";
    print >>seq_f, "  start_item(req); \n";
    print >>seq_f, "  if ( !req.randomize() )";
    print >>seq_f, "    `uvm_error(get_type_name(), \"Failed to randomize transaction\")";
    print >>seq_f, "  finish_item(req); \n";
    print >>seq_f, "  `uvm_info(get_type_name(), \"Default sequence completed\", UVM_HIGH)\n";
    print >>seq_f, "endtask : body\n";

    print >>seq_f, "`endif // "+agent_name.upper()+"_SEQ_LIB_SV\n";

    seq_f.close()
#end def gen_seq


def gen_agent_pkg(template_type):
    global project

    dir_path = project+"/dv/agent/"+agent_name+"/"
    try:
        agt_pkg_f = open( dir_path+agent_name+"_pkg.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open include file: "+agent_name
    write_file_header(agt_pkg_f)

    print >> agt_pkg_f, "`ifndef "+agent_name.upper()+"_PKG_SV";
    print >> agt_pkg_f, "`define "+agent_name.upper()+"_PKG_SV\n";

    print >> agt_pkg_f, "package "+agent_name+"_pkg;\n";
    print >> agt_pkg_f, "  import uvm_pkg::*;\n";
    print >> agt_pkg_f, "  `include \"uvm_macros.svh\"";
    print >> agt_pkg_f, "  `include \""+agent_item+".sv\"";
    print >> agt_pkg_f, "  `include \""+agent_name+"_agent_config.sv\"";
    print >> agt_pkg_f, "  `include \""+agent_name+"_monitor.sv\"";

    if(template_type == "act"):
        print >> agt_pkg_f, "  `include \""+agent_name+"_driver.sv\"\n";
        print >> agt_pkg_f, "  `include \""+agent_name+"_sequencer.sv\"";
        #print >> agt_pkg_f, "  `include \""+agent_name+"_coverage.sv\"\n";
        print >> agt_pkg_f, "  `include \""+agent_name+"_seq.sv\"\n";

    print >> agt_pkg_f, "  `include \""+agent_name+"_agent.sv\"\n";
    print >> agt_pkg_f, "endpackage : "+agent_name+"_pkg\n";
    print >> agt_pkg_f, "`endif // "+agent_name.upper()+"_PKG_SV\n";

    agt_pkg_f.close();
#end def gen_agent_pkg

def gen_top_config():
    global project
    global envname

    dir_path = project+"/dv/env/";
    try:
        env_cfg_f = open( dir_path+envname+"_config.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open config: "+envname
    write_file_header(env_cfg_f)

    print >>env_cfg_f, "`ifndef "+envname.upper()+"_CONFIG_SV"
    print >>env_cfg_f, "`define "+envname.upper()+"_CONFIG_SV\n"

    print >>env_cfg_f, "class "+envname+"_config extends uvm_object;"
    print >>env_cfg_f, "  `uvm_object_utils("+envname+"_config)\n"
    print >>env_cfg_f, "  extern function new(string name = \""+envname+"_config\");\n"
    print >>env_cfg_f, "endclass : "+envname+"_config \n"

    print >>env_cfg_f, "function "+envname+"_config::new(string name = \""+envname+"_config\");"
    print >>env_cfg_f, "  super.new(name);"
    print >>env_cfg_f, "endfunction : new\n";

    print >>env_cfg_f, "`endif // "+envname.upper()+"_CONFIG_SV\n"
    env_cfg_f.close()
#end def gen_top_config


def gen_refm():
    global project
    global tbname

    dir_path = project+"/dv/env/";
    try:
        ref_f = open(dir_path+tbname+"_refm.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open file: $tbname"
    write_file_header(ref_f)

    print >>ref_f, "`ifndef " +tbname.upper()+"_REFM_SV"
    print >>ref_f, "`define " +tbname.upper()+"_REFM_SV\n"

    print >>ref_f, "class "+tbname+"_refm extends uvm_component;";
    print >>ref_f, "  `uvm_component_utils("+tbname+"_refm)\n";
    print >>ref_f, "//    uvm_analysis_imp#(uart_seq_item) uart_imp;\n";
    print >>ref_f, "  extern function new(string name, uvm_component parent);";
    print >>ref_f, "  extern task main_phase(uvm_phase phase);\n";

    print >>ref_f, "endclass : " +tbname+"_refm \n";
    print >>ref_f, "function "+tbname+"_refm::new(string name, uvm_component parent);\n";
    print >>ref_f, "  super.new(name, parent);\n";
    print >>ref_f, "endfunction : new\n";

    print >>ref_f, "task "+tbname+"_refm::main_phase(uvm_phase phase);\n\n";
    print >>ref_f, "endtask : main_phase\n";
    print >>ref_f, "`endif // "+tbname.upper()+"_REFM_SV\n\n";
    ref_f.close();
#end def gen_refm

def gen_scb():
    global project
    global tbname

    dir_path = project+"/dv/env/";
    try:
        scb_f = open(dir_path+tbname+"_scb.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open file: $tbname"

    write_file_header(scb_f)

    print >>scb_f, "`ifndef "+tbname.upper()+"_SCB_SV";
    print >>scb_f, "`define "+tbname.upper()+"_SCB_SV\n";

    print >>scb_f, "class "+tbname+"_scb extends uvm_component;";
    print >>scb_f, "  `uvm_component_utils(" +tbname+"_scb)\n";
    print >>scb_f, "  extern function new(string name, uvm_component parent);";
    print >>scb_f, "  extern task main_phase(uvm_phase phase);\n";
    print >>scb_f, "endclass : "+tbname+"_scb \n";

    print >>scb_f, "function "+tbname+"_scb::new(string name, uvm_component parent);";
    print >>scb_f, "  super.new(name, parent);";
    print >>scb_f, "endfunction : new\n";

    print >>scb_f, "task "+tbname+"_scb::main_phase(uvm_phase phase);\n";
    print >>scb_f, "endtask : main_phase\n\n";
    print >>scb_f, "`endif // " +tbname.upper()+"_SCB_SV";
    scb_f.close();
#end def gen_scb



def gen_top_env():
    global project
    global tbname

    dir_path = project+"/dv/env/"
    try:
        env_f = open(dir_path+tbname+"_env.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open file: $tbname"

    write_file_header(env_f)

    print >>env_f, "`ifndef "+tbname.upper()+"_ENV_SV";
    print >>env_f, "`define "+tbname.upper()+"_ENV_SV\n";

    print >>env_f, "class "+tbname+"_env extends uvm_env;\n";
    print >>env_f, "  `uvm_component_utils("+tbname+"_env)\n";
    for  agent in agent_list:
        print >>env_f, "  "+agent+"_agent m_"+agent+"_agent; \n";
    #print >>env_f, tbname+"_refm m_"+tbname+"_refm; \n";
    #print >>env_f, tbname+"_scb m_"+tbname+"_scb; \n";

    print >>env_f, "  extern function new(string name, uvm_component parent);"
    print >>env_f, "  extern function void build_phase(uvm_phase phase);"
    print >>env_f, "  extern function void connect_phase(uvm_phase phase);"
    print >>env_f, "  extern function void end_of_elaboration_phase(uvm_phase phase);\n"

    print >>env_f, "endclass : "+tbname+"_env \n";

    print >>env_f, "function "+tbname+"_env::new(string name, uvm_component parent);\n"
    print >>env_f, "  super.new(name, parent);\n";
    print >>env_f, "endfunction : new\n";

    print >>env_f, "function void "+tbname+"_env::build_phase(uvm_phase phase);"
    print >>env_f, "  `uvm_info(get_type_name(), \"In build_phase\", UVM_HIGH)\n"
    print >>env_f, "  //if (!uvm_config_db #("+tbname+"_env_config)::get(this, \"\", \"m_env_config\", m_env_config)) "
    print >>env_f, "  //  `uvm_error(get_type_name(), \"Unable to get "+tbname+"_env_config\")"
    for agent in agent_list: 
        print >>env_f, "  m_"+agent+"_agent = "+agent+'_agent::type_id::create("m_'+agent+'_agent", this);\n';

    #print >>env_f, "  m_refm   =  "+tbname+"_refm::type_id::create(\"m_refm\",this);"
    #print >>env_f, "  m_scb    =  "+tbname+"_scb::type_id::create(\"m_scb\",this);\n"
    print >>env_f, "endfunction : build_phase\n";

    #connect phase
    print >>env_f, "function void "+tbname+"_env::connect_phase(uvm_phase phase);\n";
    print >>env_f, "  `uvm_info(get_type_name(), \"In connect_phase\", UVM_HIGH)\n";
    print >>env_f, "endfunction : connect_phase\n";
    
    print >>env_f, "// Could print out diagnostic information, for example\n";
    print >>env_f, "function void "+tbname+"_env::end_of_elaboration_phase(uvm_phase phase);\n";
    print >>env_f, "  //uvm_top.print_topology();\n";
    print >>env_f, "  //`uvm_info(get_type_name(), $sformatf(\"Verbosity level is set to: %d\", get_report_verbosity_level()), UVM_MEDIUM)";
    print >>env_f, "  //`uvm_info(get_type_name(), \"Print all Factory overrides\", UVM_MEDIUM)";
    print >>env_f, "  //factory.print();\n";
    print >>env_f, "endfunction : end_of_elaboration_phase\n";

    print >>env_f, "`endif // "+tbname.upper()+"_ENV_SV\n\n";
    env_f.close();
#end def gen_top_env


def gen_top_test():
    global project
    global tbname

    dir_path = project+"/dv/tests/"
    try:
        top_test_f = open(dir_path+tbname+"_test_pkg.sv", "w" )
    except IOError:
        print "can't open test: "+tbname+"_test_pkg.sv"

    write_file_header(top_test_f)

    print >>top_test_f, "`ifndef "+tbname.upper()+"_TEST_PKG_SV"
    print >>top_test_f, "`define "+tbname.upper()+"_TEST_PKG_SV\n"
    print >>top_test_f, "package "+tbname+"_test_pkg;\n"
    print >>top_test_f, "  `include \"uvm_macros.svh\"\n"
    print >>top_test_f, "  import uvm_pkg::*;\n"

    for agent in agent_list:
        print >>top_test_f, "  import "+agent+"_pkg::*;\n";

    print >>top_test_f, "  import "+tbname+"_env_pkg::*;"
    print >>top_test_f, "  `include \""+tbname+"_base_test.sv\"\n"
    print >>top_test_f, "endpackage : "+tbname+"_test_pkg\n"
    print >>top_test_f, "`endif // "+tbname.upper()+"_TEST_PKG_SV\n"
    top_test_f.close();

    # define specific tests
    try:
        base_test_f = open(dir_path+tbname+"_base_test.sv" , "w")
    except IOError:
        print "Exiting due to Error: can't open test: "+tbname+"_base_test.sv"

    write_file_header(base_test_f)

    print >>base_test_f, "`ifndef "+tbname.upper()+"_BASE_TEST_SV"
    print >>base_test_f, "`define "+tbname.upper()+"_BASE_TEST_SV\n"

    print >>base_test_f, "class "+tbname+"_base_test extends uvm_test;"
    print >>base_test_f, "  `uvm_component_utils("+tbname+"_base_test)\n"
    print >>base_test_f, "  "+tbname+"_env           m_env;";
    print >>base_test_f, "  "+tbname+"_env_config    m_env_config;"

    for  agent in agent_list:
        print >>base_test_f, "  "+agent+"_agent_config  m_"+agent+"_agent_config; \n";
    print >>base_test_f, "  "+agent_list[0]+"_seq "+agent_list[0]+"_seq_i; \n";

    print >>base_test_f, "  extern function new(string name, uvm_component parent=null);"
    print >>base_test_f, "  extern function void build_phase(uvm_phase phase);"
    print >>base_test_f, "  extern function void connect_phase(uvm_phase phase);"
    print >>base_test_f, "  extern function void end_of_elaboration_phase(uvm_phase phase);"
    print >>base_test_f, "  extern task          main_phase(uvm_phase phase);\n"
    print >>base_test_f, "endclass : "+tbname+"_base_test\n";

    print >>base_test_f, "function "+tbname+"_base_test::new(string name, uvm_component parent=null);"
    print >>base_test_f, "  super.new(name, parent);"
    print >>base_test_f, "endfunction : new\n"

    print >>base_test_f, "function void "+tbname+"_base_test::build_phase(uvm_phase phase);"
    print >>base_test_f, "  m_env        = "+tbname+'_env::type_id::create("m_env", this);'
    print >>base_test_f, "  m_env_config    = "+tbname+'_env_config::type_id::create("m_env_config", this);'

    for agent in agent_list: 
        print >>base_test_f, "  m_"+agent+"_agent_config = "+agent+'_agent_config::type_id::create("m_'+agent+'_agent_config", this);\n';

    print >>base_test_f, "  void'(m_env_config.randomize());\n";
    print >>base_test_f, "  uvm_config_db#("+tbname+"_env_config)::set(this, \"*\", \"m_env_config\", m_env_config);\n";
    for agent in agent_list:
        print >>base_test_f, "  void'(m_"+agent+"_agent_config.randomize());\n";
	print >>base_test_f, "  uvm_config_db#("+agent+'_agent_config)::set(this, "m_env.*", "m_'+agent+"_agent_config\", m_"+agent+"_agent_config);\n"

    print >>base_test_f, "  "+agent_list[0]+"_seq_i = "+agent_list[0]+'_seq::type_id::create("'+agent_list[0]+'_seq_i", this); \n'
    print >>base_test_f, "endfunction : build_phase\n";

    print >>base_test_f, "function void "+tbname+"_base_test::connect_phase(uvm_phase phase);\n";
    print >>base_test_f, "endfunction : connect_phase\n";

    print >>base_test_f, "function void "+tbname+"_base_test::end_of_elaboration_phase(uvm_phase phase);\n"
    print >>base_test_f, "  uvm_top.print_topology();";
    print >>base_test_f, "  `uvm_info(get_type_name(), $sformatf(\"Verbosity level is set to: %d\", get_report_verbosity_level()), UVM_MEDIUM)"
    print >>base_test_f, "  `uvm_info(get_type_name(), \"Print all Factory overrides\", UVM_MEDIUM)"
    print >>base_test_f, "  factory.print();\n"
    print >>base_test_f, "endfunction : end_of_elaboration_phase\n"

    print >>base_test_f, "task "+tbname+"_base_test::main_phase(uvm_phase phase);\n"
    print >>base_test_f, "    super.main_phase(phase);"
    print >>base_test_f, "    phase.raise_objection(this);"
    print >>base_test_f, "    //seq.starting_phase = phase;"
    print >>base_test_f, "    #10us;"
    print >>base_test_f, "    "+agent_list[0]+"_seq_i.start(m_env.m_"+agent_list[0]+"_agent.m_sequencer);"
    print >>base_test_f, "    `uvm_info(get_type_name(), \"Hello World!\", UVM_LOW)"
    print >>base_test_f, "    phase.drop_objection(this);"
    print >>base_test_f, "endtask : main_phase\n"

    print >>base_test_f, "`endif // "+tbname.upper()+"_BASE_TEST_SV";
    base_test_f.close();

#end def gen_test_top

def gen_top_pkg():
    global project
    global tbname

    ### file list for files in sv directoru (.svh file)
    dir_path = project+"/dv/env/";
    try:
        env_pkg_f = open( dir_path+tbname+"_env_pkg.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open include file: $tbname"
    write_file_header(env_pkg_f)

    print >>env_pkg_f, "package "+tbname+"_env_pkg;\n\n";
    print >>env_pkg_f, "  `include \"uvm_macros.svh\"\n\n";
    print >>env_pkg_f, "  import uvm_pkg::*;\n\n";
    #print >>env_pkg_f, "  import regmodel_pkg::*;\n" if $regmodel;

    for agent in agent_list:
        print >>env_pkg_f, "  import "+agent+"_pkg::*;\n";
    print >>env_pkg_f, "  `include \""+tbname+"_env_config.sv\"";
    print >>env_pkg_f, "  `include \""+tbname+"_refm.sv\"";
    print >>env_pkg_f, "  `include \""+tbname+"_scb.sv\"";
    print >>env_pkg_f, "  `include \""+tbname+"_env.sv\"";
    print >>env_pkg_f, "endpackage : "+tbname+"_env_pkg\n";
    env_pkg_f.close();


def gen_top():
    global project
    global tbname
    ### generate top modules
    ###Testbench
    dir_path = project+"/dv/tb/";          
    try:
        file_f = open(dir_path+tbname+"_tb.sv", "w" )
    except IOError:
        print "Exiting due to Error: can't open include file: "+tbname+"_tb.sv"

    write_file_header(file_f)
    print >>file_f, "`timescale 1ns/1ns\n";
    print >>file_f, "module "+tbname +"_tb;\n";
    print >>file_f, "//  timeunit $timeunit;\n";
    print >>file_f, "//  timeprecision $timeprecision;\n\n";
    print >>file_f, "  `include \"uvm_macros.svh\"\n"
    print >>file_f, "  import uvm_pkg::*;\n";

    for agent in agent_list:
        print >>file_f, "  import "+agent+"_pkg::*;"
    print >>file_f, "  import "+tbname+"_test_pkg::*;"
    print >>file_f, "  import "+tbname+"_env_pkg::*;\n"

    for agent in agent_list:
        print >>file_f, "  "+agent+"_if    m_"+agent+"_if();\n";

    print >>file_f, "  ///////////////////////// \n";
    print >>file_f, "  //dut u_dut(*) \n";
    print >>file_f, "  ///////////////////////// \n";

    print >>file_f, "  // Example clock and reset declarations\n";
    print >>file_f, "  logic clock = 0;\n";
    print >>file_f, "  logic reset;\n";
    print >>file_f, "  // Example clock generator process\n";
    print >>file_f, "  always #10 clock = ~clock;\n";

    print >>file_f, "  // Example reset generator process\n";
    print >>file_f, "  initial\n";
    print >>file_f, "  begin\n";
    print >>file_f, "    reset = 0;         // Active low reset in this example\n";
    print >>file_f, "    #75 reset = 1;\n";
    print >>file_f, "  end\n";
    print >>file_f, "  initial\n";
    print >>file_f, "  begin\n";
    for agent in (agent_list): 
        print >>file_f, "    uvm_config_db #(virtual "+agent+'_if)::set(null, "*", "'+agent+'_vif", m_'+agent+"_if);\n";
    print >>file_f, "  end\n";

    print >>file_f, "  initial\n";
    print >>file_f, "  begin\n";
    print >>file_f, "    run_test();\n";
    print >>file_f, "  end\n";
    print >>file_f, "endmodule\n";
    file_f.close();


def gen_irun_script():
    dir_path = project+"/dv/sim/";
    ius_opts = "-timescale 1ns/1ns -uvm";

    try:
        ius_f = open( dir_path+"run_irun.csh", "w" )
    except IOError:
        print "Exiting due to Error: can't open file: run_irun.csh"
    print >>ius_f, "#!/bin/sh\n\n";
    #print >>ius_f, "IUS_HOME=`ncroot`\n";
    print >>ius_f, "irun "+ius_opts+" -f filelist.f -uvmhome $UVM_HOME \\"
    print >>ius_f, "  +UVM_TESTNAME="+tbname+"_base_test +UVM_VERBOSITY=UVM_FULL -l "+tbname+"_base_test.log\n";
    gen_compile_file_list()
    ius_f.close();

    ### add execute permissions for script
    os.chmod( dir_path+"run_irun.csh", 0755 )


def gen_vcs_script():
    dir_path = project+"/dv/sim/";
    vcs_f = open( dir_path+"Makefile", "w" )

    try:
        vcs_opts = "vcs -sverilog -ntb_opts uvm -debug_pp -timescale=1ns/1ns \\";
    except IOError:
        print "Exiting due to Error: can't open file: Makefile"

    print >>vcs_f, "#!/bin/sh\n\n"
    print >>vcs_f, "RTL_PATH=../../rtl"
    print >>vcs_f, "TB_PATH=../../dv"
    print >>vcs_f, "VERB=UVM_MEDIUM"
    print >>vcs_f, "SEED=1"
    print >>vcs_f, "TEST="+tbname+"_base_test\n"
    print >>vcs_f, "all: comp run\n";
    
    print >>vcs_f, "comp:";
    print >>vcs_f, "\t"+vcs_opts
    print >>vcs_f, "    -l comp.log\n"
    gen_compile_file_list()

    print >>vcs_f, "run:"
    print >>vcs_f, "\t./simv +UVM_TESTNAME=\${TEST} +UVM_VERBOSITY=\${VERB} +ntb_random_seed=\${SEED} -l \${TEST}.log\n"

    print >>vcs_f, "dve:"
    print >>vcs_f, "\tdve -vpd vcdplus.vpd&\n"

    print >>vcs_f, "clean:"
    print >>vcs_f, "\trm -rf csrc simv* "

    vcs_f.close()

    ### add execute permissions for script
    os.chmod( "Makefile", 0755 );


def gen_compile_file_list():
    global project

    dir_path = project+"/dv/sim/"
    file_f = open(dir_path+"filelist.f", "w")

    incdir = ""
    for agent in agent_list:
        incdir += "  +incdir+../agent/"+agent+"\\\n";

    incdir += "  +incdir+../tb \\\n"
    incdir += "  +incdir+../env \\\n"
    incdir += "  +incdir+../agent \\\n"
    incdir += "  +incdir+../agent/uart \\\n"
    incdir += "  +incdir+../tests \\\n"
    incdir += "  +incdir+../tests/test_seq\\\n"
    incdir += "  +incdir+../ \\\n"

    print >>file_f, incdir

    #need to compile agents before envs
    for agent in agent_list:
        print >>file_f, "  ../agent/"+agent+"/"+agent+"_pkg.sv \n";
        print >>file_f, "  ../agent/"+agent+"/"+agent+"_if.sv \n";
   
    print >>file_f, "  ../agent/"+agent_name+"/"+agent_name+"_pkg.sv \\";
    print >>file_f, "  ../env/"+tbname+"_env_pkg.sv \\";
    print >>file_f, "  ../tests/"+tbname+"_test_pkg.sv \\";
    print >>file_f, "  ../tb/"+tbname+"_tb.sv \n";
    file_f.close()


if __name__ == "__main__":
    tb_gen(sys.argv[1:])
