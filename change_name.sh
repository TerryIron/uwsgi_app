#!/bin/bash

old_name="uwsgi_app"
new_name=$1
[ "$old_name" != "" ] && [ "$new_name" != "" ] && {

    grep -r $old_name . | grep -v node_modules | grep -v "env\|egg\|build\|.git\|node_modules\|pyc" | awk -F':' '{print $1}' | awk '!a[$0]++' | xargs -I {} sed -i 's/'"${old_name}"'/'"${new_name}"'/g' {}
    mv $old_name $new_name
}

