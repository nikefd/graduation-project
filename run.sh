prog=$1

if [ -z $1 ]; then
    echo "you must provide a file"
    exit 1
fi

if [ ! -f $1 ]; then
    echo "file does not exist"
    exit 1
fi

#${prog##*.}:从$prog中删除##右侧的通配符所配的字符串，从左到右进行匹配，##为贪婪操作符
extension="${prog##*.}"
case "$extension" in
    "cpp")
	g++ $prog && ./a.out
	;;
     *)
	echo "invalid language"
	exit 1
	;;
esac
