package main

import (
    "encoding/json"
    "fmt"
    "github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type SmartContract struct { contractapi.Contract }

type AuditReceipt struct {
    AuditID      string `json:"auditId"`
    Action       string `json:"action"`
    User         string `json:"user"`
    Role         string `json:"role"`
    Timestamp    string `json:"timestamp"`
    PayloadHash  string `json:"payloadHash"`
    PreviousHash string `json:"previousHash"`
    CurrentHash  string `json:"currentHash"`
}

func (s *SmartContract) CreateAuditReceipt(ctx contractapi.TransactionContextInterface, auditPayloadJSON string) error {
    var payload map[string]interface{}
    if err := json.Unmarshal([]byte(auditPayloadJSON), &payload); err != nil { return err }
    auditID := fmt.Sprintf("%v", payload["auditId"])
    if auditID == "" || auditID == "<nil>" { return fmt.Errorf("auditId is required") }
    receipt := AuditReceipt{
        AuditID: auditID,
        Action: fmt.Sprintf("%v", payload["action"]),
        User: fmt.Sprintf("%v", payload["user"]),
        Role: fmt.Sprintf("%v", payload["role"]),
        Timestamp: fmt.Sprintf("%v", payload["timestamp"]),
        PayloadHash: fmt.Sprintf("%v", payload["payloadHash"]),
        PreviousHash: fmt.Sprintf("%v", payload["previousHash"]),
        CurrentHash: fmt.Sprintf("%v", payload["currentHash"]),
    }
    b, _ := json.Marshal(receipt)
    return ctx.GetStub().PutState(auditID, b)
}

func (s *SmartContract) ReadAuditReceipt(ctx contractapi.TransactionContextInterface, auditID string) (*AuditReceipt, error) {
    b, err := ctx.GetStub().GetState(auditID)
    if err != nil { return nil, err }
    if b == nil { return nil, fmt.Errorf("audit receipt %s not found", auditID) }
    var receipt AuditReceipt
    if err := json.Unmarshal(b, &receipt); err != nil { return nil, err }
    return &receipt, nil
}

func main() {
    chaincode, err := contractapi.NewChaincode(&SmartContract{})
    if err != nil { panic(err) }
    if err := chaincode.Start(); err != nil { panic(err) }
}
