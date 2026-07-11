import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import grpc from '@grpc/grpc-js';
import { connect, hash, signers } from '@hyperledger/fabric-gateway';

const PORT = Number(process.env.PORT || 9090);
const MSP_ID = process.env.FABRIC_MSP_ID || 'Org1MSP';
const PEER_ENDPOINT = process.env.FABRIC_PEER_ENDPOINT || 'localhost:7051';
const PEER_HOST_ALIAS = process.env.FABRIC_PEER_HOST_ALIAS || 'peer0.org1.example.com';
const CHANNEL = process.env.FABRIC_CHANNEL || 'intelguard-channel';
const CHAINCODE = process.env.FABRIC_CHAINCODE || 'auditcc';
const CERT_PATH = process.env.FABRIC_CERT_PATH;
const KEY_DIR = process.env.FABRIC_KEY_DIR;
const TLS_CERT_PATH = process.env.FABRIC_TLS_CERT_PATH;

async function firstFile(dir) {
  const files = await fs.readdir(dir);
  if (!files.length) throw new Error(`No private key found in ${dir}`);
  return path.join(dir, files[0]);
}

async function newGrpcConnection() {
  const tlsRootCert = await fs.readFile(TLS_CERT_PATH);
  const tlsCredentials = grpc.credentials.createSsl(tlsRootCert);
  return new grpc.Client(PEER_ENDPOINT, tlsCredentials, {
    'grpc.ssl_target_name_override': PEER_HOST_ALIAS,
  });
}

async function newIdentity() {
  const credentials = await fs.readFile(CERT_PATH);
  return { mspId: MSP_ID, credentials };
}

async function newSigner() {
  const keyPath = await firstFile(KEY_DIR);
  const privateKeyPem = await fs.readFile(keyPath);
  const privateKey = crypto.createPrivateKey(privateKeyPem);
  return signers.newPrivateKeySigner(privateKey);
}

async function getContract(channelName = CHANNEL, chaincodeName = CHAINCODE) {
  if (!CERT_PATH || !KEY_DIR || !TLS_CERT_PATH) {
    throw new Error('Missing Fabric certificate/key paths in .env');
  }

  const client = await newGrpcConnection();

  const gateway = connect({
    client,
    identity: await newIdentity(),
    signer: await newSigner(),
    hash: hash.sha256,
    evaluateOptions: () => ({ deadline: Date.now() + 5000 }),
    endorseOptions: () => ({ deadline: Date.now() + 15000 }),
    submitOptions: () => ({ deadline: Date.now() + 15000 }),
    commitStatusOptions: () => ({ deadline: Date.now() + 60000 }),
  });

  const network = gateway.getNetwork(channelName);
  const contract = network.getContract(chaincodeName);

  return { gateway, client, contract };
}

const app = express();
app.use(cors());
app.use(express.json({ limit: '5mb' }));

app.get('/health', (_req, res) => {
  res.json({
    ok: true,
    service: 'IntelGuard Fabric Gateway Service',
    channel: CHANNEL,
    chaincode: CHAINCODE,
    peer: PEER_ENDPOINT,
    mspId: MSP_ID
  });
});

app.post('/transactions', async (req, res) => {
  const body = req.body || {};
  const channel = body.channel || CHANNEL;
  const chaincode = body.chaincode || CHAINCODE;
  const fn = body.function || 'CreateAuditReceipt';

  const args = (body.args || []).map((arg) =>
    typeof arg === 'string' ? arg : JSON.stringify(arg)
  );

  let gateway;
  let client;

  try {
    const ctx = await getContract(channel, chaincode);
    gateway = ctx.gateway;
    client = ctx.client;

    const resultBytes = await ctx.contract.submitTransaction(fn, ...args);

    res.json({
      ok: true,
      submitted: true,
      channel,
      chaincode,
      function: fn,
      result: Buffer.from(resultBytes).toString('utf8') || null
    });
  } catch (err) {
    res.status(500).json({
      ok: false,
      submitted: false,
      error: err.message,
      channel,
      chaincode,
      function: fn
    });
  } finally {
    try { gateway?.close(); } catch {}
    try { client?.close(); } catch {}
  }
});

app.get('/receipts/:auditId', async (req, res) => {
  let gateway;
  let client;

  try {
    const ctx = await getContract(CHANNEL, CHAINCODE);
    gateway = ctx.gateway;
    client = ctx.client;

    const resultBytes = await ctx.contract.evaluateTransaction(
      'ReadAuditReceipt',
      req.params.auditId
    );

    res.type('json').send(Buffer.from(resultBytes).toString('utf8'));
  } catch (err) {
    res.status(404).json({
      ok: false,
      error: err.message
    });
  } finally {
    try { gateway?.close(); } catch {}
    try { client?.close(); } catch {}
  }
});

app.listen(PORT, () => {
  console.log(`IntelGuard Fabric Gateway Service running on http://localhost:${PORT}`);
});
