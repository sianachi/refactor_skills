namespace Catalog.Api.Common;

public class Result<T>
{
    private Result(bool success, T? value, string? error)
    {
        Success = success;
        Value = value;
        Error = error;
    }

    public bool Success { get; }

    public T? Value { get; }

    public string? Error { get; }

    public static Result<T> Ok(T value) => new(true, value, null);

    public static Result<T> Fail(string error) => new(false, default, error);
}
