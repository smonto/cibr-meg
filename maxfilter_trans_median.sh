#! /bin/bash

## Stage 1: Find the reference head position
echo ""
echo "Find middle head position ..."
# Find the files of interest
file_list=($(find ./orig/ -name "*audlex*.fif"))
echo "Found these files:"
printf '%s\n' "${file_list[@]}"
# Read xyz coordinates to lists from each file
let cnt=0
for file in ${file_list[@]}
       	do
       		hpx_list[${cnt}]=$(/opt/neuromag/bin/util/show_fiff -vt222 $file | tail -n 1 | awk {'printf "%d", $1 * 100'})
	       	hpy_list[${cnt}]=$(/opt/neuromag/bin/util/show_fiff -vt222 $file | tail -n 1 | awk {'printf "%d", $2 * 100'})
       		hpz_list[${cnt}]=$(/opt/neuromag/bin/util/show_fiff -vt222 $file | tail -n 1 | awk {'printf "%d", $3 * 100'})
       		((cnt++))
       	done
# Sort coordinates (across subjects)
for i in $(seq 0 $((${#file_list[@]}-1)))
do
	let cntx=0
	let cnty=0
	let cntz=0
	for j in $(seq 0 $((${#file_list[@]}-1)))
	do
		if [ ${hpx_list[${i}]} -gt ${hpx_list[${j}]} ]; then ((cntx++)); fi
		if [ ${hpy_list[${i}]} -gt ${hpy_list[${j}]} ]; then ((cnty++)); fi
		if [ ${hpz_list[${i}]} -gt ${hpz_list[${j}]} ]; then ((cntz++)); fi
	done
	# Subtract mean
	let hpx_sort[${i}]=${cntx}-$((${#file_list[@]}/2))
	let hpy_sort[${i}]=${cnty}-$((${#file_list[@]}/2))
	let hpz_sort[${i}]=${cntz}-$((${#file_list[@]}/2))
	# Set abs value
	if [ "${hpx_sort[${i}]}" -lt "0" ]; then let hpx_sort[${i}]=-1*${hpx_sort[${i}]}; fi
	if [ "${hpy_sort[${i}]}" -lt "0" ]; then let hpy_sort[${i}]=-1*${hpy_sort[${i}]}; fi
	if [ "${hpz_sort[${i}]}" -lt "0" ]; then let hpz_sort[${i}]=-1*${hpz_sort[${i}]}; fi
	# Sum values
	let hp_sort[${i}]=$((${hpx_sort[${i}]}+${hpy_sort[${i}]}+${hpz_sort[${i}]}))
	echo "hp_sort = ${hp_sort[${i}]}"
done
# Find coordinates that are closest to median across subjects
let hp_min_val=10000
let hp_min_ind=-1
for i in $(seq 0 $((${#file_list[@]}-1)))
do
	if [ "${hp_sort[${i}]}" -lt "${hp_min_val}" ] ; then
		let hp_min_val=${hp_sort[${i}]}
		let hp_min_ind=${i}
		echo "set hp min ind = $hp_min_ind"
	fi
done
# The common head position file
#hp_file=${file_list[${hp_min_ind}]} | sed 's/^.//g'
hp_file=${file_list[${hp_min_ind}]}
echo "Compromise head position file: $hp_file"
echo "Total ranks from median position: $hp_min_val"
cp "$hp_file" "scripts/med.fif"

