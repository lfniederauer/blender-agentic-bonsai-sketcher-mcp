# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Apply the .env file to the environment not using source becaue i don know
# how to do it in a shell script

# get the path to the .env file
ENV_FILE=".env"

# read the .env file and apply the variables to the environment
while IFS='=' read -r key value; do
    export "$key=$value"
done < "$ENV_FILE"
