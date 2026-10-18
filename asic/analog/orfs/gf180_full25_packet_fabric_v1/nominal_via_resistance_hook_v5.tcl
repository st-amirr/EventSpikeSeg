# GF180 nominal4500milliohm/contact from local open_pdks gf180mcuD.tech.
foreach v {Via1 Via2 Via3 Via4} {
 set_layer_rc -via $v -resistance 4.5
 set layer [[ord::get_db_tech] findLayer $v]
 $layer setResistance 4.5
 puts "NOMINAL_VIA_RESISTANCE $v [$layer getResistance] ohm"
}
