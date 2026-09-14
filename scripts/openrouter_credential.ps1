param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Set', 'Get', 'Test', 'Remove')]
    [string]$Action
)

$ErrorActionPreference = 'Stop'
$targetName = 'Codex/OpenRouter'

if (-not ('OpenRouterCredential.NativeMethods' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

namespace OpenRouterCredential
{
    public static class NativeMethods
    {
        public const int CRED_TYPE_GENERIC = 1;
        public const int CRED_PERSIST_LOCAL_MACHINE = 2;
        public const int ERROR_NOT_FOUND = 1168;

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct CREDENTIAL
        {
            public UInt32 Flags;
            public UInt32 Type;
            public string TargetName;
            public string Comment;
            public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
            public UInt32 CredentialBlobSize;
            public IntPtr CredentialBlob;
            public UInt32 Persist;
            public UInt32 AttributeCount;
            public IntPtr Attributes;
            public string TargetAlias;
            public string UserName;
        }

        [DllImport("advapi32.dll", EntryPoint = "CredWriteW", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool CredWrite(ref CREDENTIAL credential, UInt32 flags);

        [DllImport("advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool CredRead(string target, UInt32 type, UInt32 flags, out IntPtr credential);

        [DllImport("advapi32.dll", EntryPoint = "CredDeleteW", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool CredDelete(string target, UInt32 type, UInt32 flags);

        [DllImport("advapi32.dll")]
        public static extern void CredFree(IntPtr buffer);
    }
}
'@
}

function Get-NativeCredentialPointer {
    $credentialPointer = [IntPtr]::Zero
    $found = [OpenRouterCredential.NativeMethods]::CredRead(
        $targetName,
        [OpenRouterCredential.NativeMethods]::CRED_TYPE_GENERIC,
        0,
        [ref]$credentialPointer
    )
    if (-not $found) {
        $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
        if ($errorCode -eq [OpenRouterCredential.NativeMethods]::ERROR_NOT_FOUND) {
            throw "Credential '$targetName' was not found in Windows Credential Manager."
        }
        throw "CredRead failed with Windows error $errorCode."
    }
    return $credentialPointer
}

switch ($Action) {
    'Set' {
        Write-Host 'Enter the dedicated OpenRouter key below. Secure input will not be displayed.'
        $secret = Read-Host 'OpenRouter API key' -AsSecureString
        $secretPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
        try {
            $blobSize = [Runtime.InteropServices.Marshal]::ReadInt32($secretPointer, -4)
            if ($blobSize -le 0) {
                throw 'The API key cannot be empty.'
            }
            if ($blobSize -gt 2560) {
                throw 'The API key is too large for a generic Windows credential.'
            }
            $credential = New-Object OpenRouterCredential.NativeMethods+CREDENTIAL
            $credential.Flags = 0
            $credential.Type = [OpenRouterCredential.NativeMethods]::CRED_TYPE_GENERIC
            $credential.TargetName = $targetName
            $credential.Comment = 'Dedicated OpenRouter API key for Codex external agents'
            $credential.CredentialBlobSize = $blobSize
            $credential.CredentialBlob = $secretPointer
            $credential.Persist = [OpenRouterCredential.NativeMethods]::CRED_PERSIST_LOCAL_MACHINE
            $credential.AttributeCount = 0
            $credential.Attributes = [IntPtr]::Zero
            $credential.TargetAlias = $null
            $credential.UserName = 'openrouter'
            if (-not [OpenRouterCredential.NativeMethods]::CredWrite([ref]$credential, 0)) {
                $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
                throw "CredWrite failed with Windows error $errorCode."
            }
        } finally {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secretPointer)
            $secret.Dispose()
        }
        Write-Output "Stored '$targetName' in Windows Credential Manager."
    }
    'Get' {
        $credentialPointer = Get-NativeCredentialPointer
        try {
            $credential = [Runtime.InteropServices.Marshal]::PtrToStructure(
                $credentialPointer,
                [type][OpenRouterCredential.NativeMethods+CREDENTIAL]
            )
            if ($credential.CredentialBlobSize -eq 0) {
                throw "Credential '$targetName' is empty."
            }
            $value = [Runtime.InteropServices.Marshal]::PtrToStringUni(
                $credential.CredentialBlob,
                [int]($credential.CredentialBlobSize / 2)
            )
            Write-Output $value
        } finally {
            if ($credentialPointer -ne [IntPtr]::Zero) {
                [OpenRouterCredential.NativeMethods]::CredFree($credentialPointer)
            }
        }
    }
    'Test' {
        $credentialPointer = Get-NativeCredentialPointer
        try {
            Write-Output "Credential '$targetName' is present."
        } finally {
            [OpenRouterCredential.NativeMethods]::CredFree($credentialPointer)
        }
    }
    'Remove' {
        if (-not [OpenRouterCredential.NativeMethods]::CredDelete(
            $targetName,
            [OpenRouterCredential.NativeMethods]::CRED_TYPE_GENERIC,
            0
        )) {
            $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
            if ($errorCode -eq [OpenRouterCredential.NativeMethods]::ERROR_NOT_FOUND) {
                Write-Output "Credential '$targetName' was already absent."
                break
            }
            throw "CredDelete failed with Windows error $errorCode."
        }
        Write-Output "Removed '$targetName' from Windows Credential Manager."
    }
}
