package convert

// Converter converts between temperature scales.
type Converter interface {
	CToF(c float64) float64
	FToC(f float64) float64
}

type standardConverter struct{}

func (standardConverter) CToF(c float64) float64 { return c*9/5 + 32 }
func (standardConverter) FToC(f float64) float64 { return (f - 32) * 5 / 9 }

// NewConverter returns a converter for the given kind. Only "standard" exists.
func NewConverter(kind string) Converter {
	switch kind {
	case "standard":
		return standardConverter{}
	default:
		return standardConverter{}
	}
}

func round2(v float64) float64 {
	return float64(int(v*100)) / 100
}
