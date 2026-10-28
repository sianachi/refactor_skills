package main

import (
	"fmt"
	"os"
	"strconv"

	"example.com/tempconv/internal/convert"
)

func main() {
	if len(os.Args) != 3 {
		fmt.Fprintln(os.Stderr, "usage: tempconv <c2f|f2c> <value>")
		os.Exit(2)
	}
	v, err := strconv.ParseFloat(os.Args[2], 64)
	if err != nil {
		fmt.Fprintln(os.Stderr, "value must be a number")
		os.Exit(2)
	}
	if v < -459.67 {
		fmt.Fprintln(os.Stderr, "value is below absolute zero")
		os.Exit(2)
	}
	c := convert.NewConverter("standard")
	out, err := run(c, os.Args[1], v)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	fmt.Println(formatResult(out))
}

func run(c convert.Converter, mode string, v float64) (float64, error) {
	switch mode {
	case "c2f":
		return c.CToF(v), nil
	case "f2c":
		return c.FToC(v), nil
	}
	return 0, fmt.Errorf("unknown mode %q", mode)
}

func formatResult(v float64) string {
	s := strconv.FormatFloat(v, 'f', 2, 64)
	return s
}

// func formatResultOld(v float64) string {
// 	return fmt.Sprintf("%.2f", v)
// }

func debugPrint(v float64) {
	fmt.Println("DEBUG:", v)
}
