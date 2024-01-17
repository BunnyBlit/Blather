# I should also chain relative urls here but that's too anoying with pelican at the moment,
# so the only arg I accept is debug
pelican_opts := if env_var_or_default('DEBUG', '0') == '1' { "-D" } else { "" }

base_dir := justfile_directory()
src_dir := base_dir + "/src"
# input to pelican, this should be a directory of markdown and static assets
input_dir := base_dir + "/content"
output_dir := base_dir + "/output"
conf_file := base_dir + "/pelicanconf.py"
publish_conf := base_dir + "/publishconf.py"

ssh_host := "suspendedsunlight.dev"
ssh_user := "pix"
ssh_target_dir := "/var/www/html"
ssh_identity := env_var('BLOG_PUBLISH_KEY_FILE')


# still have a lot of other stuff to do before this whole kit and kabootle work
# opts and relative need to get figured out, along with port
server := "0.0.0.0"

default: help
help:
    @just --list

markdown:
    #!/usr/bin/env bash
    set -euxo pipefail
    for input_notebook in "{{src_dir}}/*.ipynb"; do
        # execute, then convert-- we still need to run cells ignored in the conversion, hence two steps
        jupyter nbconvert --to notebook --execute --inplace "$input_notebook"
        jupyter nbconvert --to markdown --output-dir "{{input_dir}}" --TagRemovePreprocessor.enabled=True --TagRemovePreprocessor.remove_cell_tags ignore_cell "$input_notebook"
    done

html: markdown
    pelican "{{input_dir}}" -o "{{output_dir}}" -s "{{conf_file}}" {{pelican_opts}}

clean:
    rm -r "{{output_dir}}"

regenerate:
    pelican -r "{{input_dir}}" -o "{{output_dir}}" -s "{{conf_file}}" {{pelican_opts}}

serve:
    pelican -l "{{input_dir}}" -o "{{output_dir}}" -s "{{conf_file}}" {{pelican_opts}}

serve-global:
    pelican -l "{{input_dir}}" -o "{{output_dir}}" -s "{{conf_file}}" {{pelican_opts}} -b {{server}}

devserver:
    pelican -l "{{input_dir}}" -o "{{output_dir}}" -s "{{conf_file}}" {{pelican_opts}}

devserver-global:
    pelican -l "{{input_dir}}" -o "{{output_dir}}" -s "{{conf_file}}" {{pelican_opts}} -b 0.0.0.0 

publish: markdown
    pelican "{{input_dir}}" -o "{{output_dir}}" -s "{{publish_conf}}" {{pelican_opts}}

upload: publish
    rsync -e "ssh -i {{ssh_identity}}" -P -rvzc --include tags --cvs-exclude --delete "{{output_dir}}/" "{{ssh_user}}@{{ssh_host}}:{{ssh_target_dir}}"