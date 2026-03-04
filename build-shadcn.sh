#! /bin/bash
if xar -h &> /dev/null
then
    echo "xar could not be found"
else

    xar -cf proof_shadcn_theme.fmaddon proof_shadcn_theme/
    echo 'build succesful'
fi
